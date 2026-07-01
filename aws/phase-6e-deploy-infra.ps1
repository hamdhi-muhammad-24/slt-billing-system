[CmdletBinding()]
param(
    [string]$Region = "ap-southeast-1",
    [string]$AccountId = "",
    [string]$ClusterName = "slt-cluster",
    [string]$VpcId = "",
    [string[]]$SubnetIds = @(),
    [string]$AlbName = "slt-billing-alb",
    [string]$TargetGroupName = "slt-backend-tg",
    [string]$AlbSecurityGroupName = "slt-alb-sg",
    [string]$EcsSecurityGroupName = "slt-ecs-tasks-sg",
    [string]$BackendServiceName = "slt-backend-service",
    [string]$WorkerServiceName = "slt-worker-service",
    [string]$BeatServiceName = "slt-beat-service",
    [string]$BackendTaskDefinition = "slt-backend",
    [string]$WorkerTaskDefinition = "slt-worker",
    [string]$BeatTaskDefinition = "slt-beat",
    [string]$BackendTaskDefinitionFile = "",
    [string]$WorkerTaskDefinitionFile = "",
    [string]$BeatTaskDefinitionFile = "",
    [string]$BackendContainerName = "slt-backend",
    [string]$RdsIdentifier = "slt-billing-db",
    [string]$RedisClusterId = "slt-redis",
    [string]$FrontendBucket = "",
    [string]$CertificateArn = "",
    [string]$DomainName = "",
    [int]$BackendDesiredCount = 1,
    [int]$WorkerDesiredCount = 1,
    [int]$BeatDesiredCount = 1
)

$ErrorActionPreference = "Stop"

function Invoke-AwsText {
    param([object[]]$AwsArgs)

    $output = & aws @AwsArgs --region $Region --output text 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "aws $($AwsArgs -join ' ') failed: $($output | Out-String)"
    }

    return (($output | Out-String).Trim())
}

function Invoke-AwsJson {
    param([object[]]$AwsArgs)

    $output = & aws @AwsArgs --region $Region --output json 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "aws $($AwsArgs -join ' ') failed: $($output | Out-String)"
    }

    $text = ($output | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($text)) {
        return $null
    }

    return $text | ConvertFrom-Json
}

function Invoke-AwsNoOutput {
    param([object[]]$AwsArgs)

    $output = & aws @AwsArgs --region $Region 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "aws $($AwsArgs -join ' ') failed: $($output | Out-String)"
    }
}

function Invoke-AwsIgnoreDuplicate {
    param([object[]]$AwsArgs)

    $output = & aws @AwsArgs --region $Region 2>&1
    if ($LASTEXITCODE -ne 0) {
        $text = ($output | Out-String)
        if ($text -notmatch "InvalidPermission\.Duplicate") {
            throw "aws $($AwsArgs -join ' ') failed: $text"
        }
    }
}

function Test-Missing {
    param([string]$Value)
    return [string]::IsNullOrWhiteSpace($Value) -or $Value -eq "None" -or $Value -eq "null"
}

function Write-TempJson {
    param([object]$Object)

    $path = [System.IO.Path]::GetTempFileName()
    $json = $Object | ConvertTo-Json -Depth 40
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($path, $json, $utf8NoBom)
    return $path
}

function Write-TempText {
    param([string]$Text)

    $path = [System.IO.Path]::GetTempFileName()
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($path, $Text, $utf8NoBom)
    return $path
}

function ConvertTo-AwsFileUri {
    param(
        [string]$Path,
        [switch]$Binary
    )

    $resolved = Resolve-Path -LiteralPath $Path
    $prefix = "file:///"
    if ($Binary) {
        $prefix = "fileb:///"
    }
    return $prefix + ($resolved.ProviderPath -replace "\\", "/")
}

function Ensure-SecurityGroup {
    param(
        [string]$GroupName,
        [string]$Description
    )

    $groupId = Invoke-AwsText @(
        "ec2", "describe-security-groups",
        "--filters", "Name=group-name,Values=$GroupName", "Name=vpc-id,Values=$VpcId",
        "--query", "SecurityGroups[0].GroupId"
    )

    if (Test-Missing $groupId) {
        Write-Host "Creating security group $GroupName"
        $groupId = Invoke-AwsText @(
            "ec2", "create-security-group",
            "--group-name", $GroupName,
            "--description", $Description,
            "--vpc-id", $VpcId,
            "--query", "GroupId"
        )
    }
    else {
        Write-Host "Security group $GroupName already exists: $groupId"
    }

    return $groupId
}

function Add-IngressFromCidr {
    param(
        [string]$GroupId,
        [int]$Port,
        [string]$Cidr
    )

    Invoke-AwsIgnoreDuplicate @(
        "ec2", "authorize-security-group-ingress",
        "--group-id", $GroupId,
        "--protocol", "tcp",
        "--port", $Port,
        "--cidr", $Cidr
    )
}

function Add-IngressFromSecurityGroup {
    param(
        [string]$GroupId,
        [int]$Port,
        [string]$SourceGroupId
    )

    Invoke-AwsIgnoreDuplicate @(
        "ec2", "authorize-security-group-ingress",
        "--group-id", $GroupId,
        "--protocol", "tcp",
        "--port", $Port,
        "--source-group", $SourceGroupId
    )
}

function Ensure-LoadBalancer {
    try {
        $existing = Invoke-AwsJson @("elbv2", "describe-load-balancers", "--names", $AlbName, "--query", "LoadBalancers[0]")
        if ($null -ne $existing) {
            Write-Host "ALB already exists: $($existing.DNSName)"
            return $existing
        }
    }
    catch {
        Write-Host "ALB $AlbName does not exist yet."
    }

    Write-Host "Creating ALB $AlbName"
    $args = @(
        "elbv2", "create-load-balancer",
        "--name", $AlbName,
        "--subnets"
    ) + $SubnetIds + @(
        "--security-groups", $AlbSecurityGroupId,
        "--scheme", "internet-facing",
        "--type", "application",
        "--ip-address-type", "ipv4",
        "--query", "LoadBalancers[0]"
    )

    return Invoke-AwsJson $args
}

function Ensure-TargetGroup {
    try {
        $existing = Invoke-AwsJson @("elbv2", "describe-target-groups", "--names", $TargetGroupName, "--query", "TargetGroups[0]")
        if ($null -ne $existing) {
            Write-Host "Target group already exists: $($existing.TargetGroupArn)"
            return $existing
        }
    }
    catch {
        Write-Host "Target group $TargetGroupName does not exist yet."
    }

    Write-Host "Creating target group $TargetGroupName"
    return Invoke-AwsJson @(
        "elbv2", "create-target-group",
        "--name", $TargetGroupName,
        "--protocol", "HTTP",
        "--port", "8000",
        "--vpc-id", $VpcId,
        "--target-type", "ip",
        "--health-check-protocol", "HTTP",
        "--health-check-path", "/health",
        "--health-check-interval-seconds", "30",
        "--health-check-timeout-seconds", "5",
        "--healthy-threshold-count", "2",
        "--unhealthy-threshold-count", "3",
        "--matcher", "HttpCode=200",
        "--query", "TargetGroups[0]"
    )
}

function Ensure-HttpListener {
    param(
        [string]$LoadBalancerArn,
        [string]$TargetGroupArn
    )

    $listeners = Invoke-AwsJson @("elbv2", "describe-listeners", "--load-balancer-arn", $LoadBalancerArn)
    $httpListener = @($listeners.Listeners | Where-Object { $_.Port -eq 80 }) | Select-Object -First 1
    if ($null -ne $httpListener) {
        Write-Host "HTTP listener already exists."
        return
    }

    Write-Host "Creating HTTP listener on port 80"
    Invoke-AwsNoOutput @(
        "elbv2", "create-listener",
        "--load-balancer-arn", $LoadBalancerArn,
        "--protocol", "HTTP",
        "--port", "80",
        "--default-actions", "Type=forward,TargetGroupArn=$TargetGroupArn"
    )
}

function Ensure-HttpsListener {
    param(
        [string]$LoadBalancerArn,
        [string]$TargetGroupArn,
        [string]$AcmCertificateArn
    )

    if (Test-Missing $AcmCertificateArn) {
        Write-Host "No ACM certificate provided for ALB HTTPS. CloudFront will still serve HTTPS to users."
        return
    }

    $listeners = Invoke-AwsJson @("elbv2", "describe-listeners", "--load-balancer-arn", $LoadBalancerArn)
    $httpsListener = @($listeners.Listeners | Where-Object { $_.Port -eq 443 }) | Select-Object -First 1
    if ($null -ne $httpsListener) {
        Write-Host "HTTPS listener already exists."
        return
    }

    Write-Host "Creating HTTPS listener on port 443"
    Add-IngressFromCidr -GroupId $AlbSecurityGroupId -Port 443 -Cidr "0.0.0.0/0"
    Invoke-AwsNoOutput @(
        "elbv2", "create-listener",
        "--load-balancer-arn", $LoadBalancerArn,
        "--protocol", "HTTPS",
        "--port", "443",
        "--certificates", "CertificateArn=$AcmCertificateArn",
        "--default-actions", "Type=forward,TargetGroupArn=$TargetGroupArn"
    )
}

function Get-ServiceStatus {
    param([string]$ServiceName)

    return Invoke-AwsText @(
        "ecs", "describe-services",
        "--cluster", $ClusterName,
        "--services", $ServiceName,
        "--query", "services[0].status"
    )
}

function Ensure-EcsService {
    param(
        [string]$ServiceName,
        [string]$TaskDefinition,
        [int]$DesiredCount,
        [switch]$AttachLoadBalancer
    )

    $taskDefinitionArn = Invoke-AwsText @(
        "ecs", "describe-task-definition",
        "--task-definition", $TaskDefinition,
        "--query", "taskDefinition.taskDefinitionArn"
    )
    $networkConfig = "awsvpcConfiguration={subnets=[$($SubnetIds -join ',')],securityGroups=[$EcsSecurityGroupId],assignPublicIp=ENABLED}"
    $status = Get-ServiceStatus -ServiceName $ServiceName

    if ($status -eq "ACTIVE") {
        Write-Host "Updating ECS service $ServiceName"
        Invoke-AwsNoOutput @(
            "ecs", "update-service",
            "--cluster", $ClusterName,
            "--service", $ServiceName,
            "--task-definition", $taskDefinitionArn,
            "--desired-count", $DesiredCount,
            "--force-new-deployment"
        )
        return
    }

    Write-Host "Creating ECS service $ServiceName"
    $args = @(
        "ecs", "create-service",
        "--cluster", $ClusterName,
        "--service-name", $ServiceName,
        "--task-definition", $taskDefinitionArn,
        "--desired-count", $DesiredCount,
        "--launch-type", "FARGATE",
        "--platform-version", "LATEST",
        "--network-configuration", $networkConfig
    )

    if ($AttachLoadBalancer) {
        $args += @(
            "--load-balancers",
            "targetGroupArn=$TargetGroupArn,containerName=$BackendContainerName,containerPort=8000",
            "--health-check-grace-period-seconds", "120"
        )
    }

    Invoke-AwsNoOutput $args
}

function Register-TaskDefinitionFile {
    param([string]$Path)

    $resolved = Resolve-Path -LiteralPath $Path
    $fileUri = ConvertTo-AwsFileUri -Path $resolved.ProviderPath
    Write-Host "Registering task definition $($resolved.ProviderPath)"
    return Invoke-AwsText @(
        "ecs", "register-task-definition",
        "--cli-input-json", $fileUri,
        "--query", "taskDefinition.taskDefinitionArn"
    )
}

function Resolve-RedisCacheClusterId {
    try {
        $cacheClusterId = Invoke-AwsText @(
            "elasticache", "describe-cache-clusters",
            "--cache-cluster-id", $RedisClusterId,
            "--show-cache-node-info",
            "--query", "CacheClusters[0].CacheClusterId"
        )
        if (-not (Test-Missing $cacheClusterId)) {
            return $cacheClusterId
        }
    }
    catch {
        Write-Host "Redis cache cluster $RedisClusterId not found directly. Checking replication groups."
    }

    $memberClusterId = Invoke-AwsText @(
        "elasticache", "describe-replication-groups",
        "--replication-group-id", $RedisClusterId,
        "--query", "ReplicationGroups[0].MemberClusters[0]"
    )
    if (Test-Missing $memberClusterId) {
        throw "Could not resolve Redis cache cluster from $RedisClusterId."
    }

    return $memberClusterId
}

function Ensure-FrontendBucket {
    if ([string]::IsNullOrWhiteSpace($FrontendBucket)) {
        $script:FrontendBucket = "slt-billing-frontend-$AccountId-$Region"
    }

    $head = & aws s3api head-bucket --bucket $FrontendBucket --region $Region 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Creating frontend S3 bucket $FrontendBucket"
        Invoke-AwsNoOutput @(
            "s3api", "create-bucket",
            "--bucket", $FrontendBucket,
            "--create-bucket-configuration", "LocationConstraint=$Region"
        )
    }
    else {
        Write-Host "Frontend S3 bucket already exists: $FrontendBucket"
    }

    Invoke-AwsNoOutput @(
        "s3api", "put-public-access-block",
        "--bucket", $FrontendBucket,
        "--public-access-block-configuration",
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    )
}

function Ensure-OriginAccessControl {
    $oacName = "slt-billing-frontend-oac"
    $oacId = Invoke-AwsText @(
        "cloudfront", "list-origin-access-controls",
        "--query", "OriginAccessControlList.Items[?Name=='$oacName'].Id | [0]"
    )

    if (-not (Test-Missing $oacId)) {
        Write-Host "CloudFront origin access control already exists: $oacId"
        return $oacId
    }

    Write-Host "Creating CloudFront origin access control"
    $oacConfig = [ordered]@{
        Name = $oacName
        Description = "Private S3 access for SLT Billing frontend"
        SigningProtocol = "sigv4"
        SigningBehavior = "always"
        OriginAccessControlOriginType = "s3"
    }
    $oacConfigPath = Write-TempJson $oacConfig
    $oac = Invoke-AwsJson @(
        "cloudfront", "create-origin-access-control",
        "--origin-access-control-config", "file://$oacConfigPath",
        "--query", "OriginAccessControl"
    )
    Remove-Item -LiteralPath $oacConfigPath -Force
    return $oac.Id
}

function New-ApiCacheBehavior {
    param([string]$PathPattern)

    return [ordered]@{
        PathPattern = $PathPattern
        TargetOriginId = "alb-backend"
        ViewerProtocolPolicy = "redirect-to-https"
        AllowedMethods = [ordered]@{
            Quantity = 7
            Items = @("GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE")
            CachedMethods = [ordered]@{
                Quantity = 3
                Items = @("GET", "HEAD", "OPTIONS")
            }
        }
        Compress = $true
        CachePolicyId = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
        OriginRequestPolicyId = "b689b0a8e-53d0-40ab-baf-68738e2966ac"
    }
}

function Ensure-CloudFrontFunction {
    $functionName = "slt-billing-spa-rewrite"

    try {
        $live = Invoke-AwsJson @(
            "cloudfront", "describe-function",
            "--name", $functionName,
            "--stage", "LIVE",
            "--query", "FunctionSummary"
        )
        if ($null -ne $live) {
            Write-Host "CloudFront Function already exists: $functionName"
            return $live.FunctionMetadata.FunctionARN
        }
    }
    catch {
        Write-Host "CloudFront Function $functionName does not exist in LIVE stage yet."
    }

    $functionCode = @'
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    if (uri.indexOf('.') === -1) {
        request.uri = '/index.html';
    }

    return request;
}
'@
    $codePath = Write-TempText $functionCode
    $codeUri = ConvertTo-AwsFileUri -Path $codePath -Binary

    try {
        Write-Host "Creating CloudFront Function $functionName"
        $created = Invoke-AwsJson @(
            "cloudfront", "create-function",
            "--name", $functionName,
            "--function-config", "Comment=SLT Billing SPA route rewrite,Runtime=cloudfront-js-1.0",
            "--function-code", $codeUri
        )
        $etag = $created.ETag
    }
    catch {
        Write-Host "CloudFront Function already exists in DEVELOPMENT. Publishing existing version."
        $development = Invoke-AwsJson @(
            "cloudfront", "describe-function",
            "--name", $functionName,
            "--stage", "DEVELOPMENT"
        )
        $etag = $development.ETag
    }
    finally {
        Remove-Item -LiteralPath $codePath -Force
    }

    $published = Invoke-AwsJson @(
        "cloudfront", "publish-function",
        "--name", $functionName,
        "--if-match", $etag,
        "--query", "FunctionSummary"
    )
    return $published.FunctionMetadata.FunctionARN
}

function Ensure-CloudFrontDistribution {
    param(
        [string]$AlbDnsName,
        [string]$OacId,
        [string]$FunctionArn
    )

    $distributionComment = "SLT Billing frontend and API"
    $distributionId = Invoke-AwsText @(
        "cloudfront", "list-distributions",
        "--query", "DistributionList.Items[?Comment=='$distributionComment'].Id | [0]"
    )

    if (-not (Test-Missing $distributionId)) {
        $domain = Invoke-AwsText @("cloudfront", "get-distribution", "--id", $distributionId, "--query", "Distribution.DomainName")
        Write-Host "CloudFront distribution already exists: $distributionId"
        return [pscustomobject]@{
            Id = $distributionId
            DomainName = $domain
        }
    }

    Write-Host "Creating CloudFront distribution for frontend and API"
    $apiPatterns = @(
        "/auth*",
        "/health",
        "/customers*",
        "/accounts*",
        "/service-accounts*",
        "/invoices*",
        "/billing*",
        "/docs*",
        "/redoc*",
        "/openapi.json"
    )
    $apiBehaviors = @($apiPatterns | ForEach-Object { New-ApiCacheBehavior -PathPattern $_ })

    $aliases = [ordered]@{ Quantity = 0 }
    $viewerCertificate = [ordered]@{
        CloudFrontDefaultCertificate = $true
        MinimumProtocolVersion = "TLSv1"
        CertificateSource = "cloudfront"
    }

    if (-not (Test-Missing $DomainName) -and -not (Test-Missing $CertificateArn)) {
        $aliases = [ordered]@{
            Quantity = 1
            Items = @($DomainName)
        }
        $viewerCertificate = [ordered]@{
            ACMCertificateArn = $CertificateArn
            SSLSupportMethod = "sni-only"
            MinimumProtocolVersion = "TLSv1.2_2021"
            CertificateSource = "acm"
        }
    }

    $distributionConfig = [ordered]@{
        CallerReference = "slt-billing-$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"
        Comment = $distributionComment
        Enabled = $true
        IsIPV6Enabled = $true
        HttpVersion = "http2"
        PriceClass = "PriceClass_200"
        DefaultRootObject = "index.html"
        Aliases = $aliases
        Origins = [ordered]@{
            Quantity = 2
            Items = @(
                [ordered]@{
                    Id = "s3-frontend"
                    DomainName = "$FrontendBucket.s3.$Region.amazonaws.com"
                    OriginAccessControlId = $OacId
                    S3OriginConfig = [ordered]@{
                        OriginAccessIdentity = ""
                    }
                },
                [ordered]@{
                    Id = "alb-backend"
                    DomainName = $AlbDnsName
                    CustomOriginConfig = [ordered]@{
                        HTTPPort = 80
                        HTTPSPort = 443
                        OriginProtocolPolicy = "http-only"
                        OriginSslProtocols = [ordered]@{
                            Quantity = 1
                            Items = @("TLSv1.2")
                        }
                        OriginReadTimeout = 30
                        OriginKeepaliveTimeout = 5
                    }
                }
            )
        }
        DefaultCacheBehavior = [ordered]@{
            TargetOriginId = "s3-frontend"
            ViewerProtocolPolicy = "redirect-to-https"
            AllowedMethods = [ordered]@{
                Quantity = 2
                Items = @("GET", "HEAD")
                CachedMethods = [ordered]@{
                    Quantity = 2
                    Items = @("GET", "HEAD")
                }
            }
            Compress = $true
            CachePolicyId = "658327ea-f89d-4fab-a63d-7e88639e58f6"
            FunctionAssociations = [ordered]@{
                Quantity = 1
                Items = @(
                    [ordered]@{
                        EventType = "viewer-request"
                        FunctionARN = $FunctionArn
                    }
                )
            }
        }
        CacheBehaviors = [ordered]@{
            Quantity = $apiBehaviors.Count
            Items = $apiBehaviors
        }
        CustomErrorResponses = [ordered]@{
            Quantity = 0
        }
        Restrictions = [ordered]@{
            GeoRestriction = [ordered]@{
                RestrictionType = "none"
                Quantity = 0
            }
        }
        ViewerCertificate = $viewerCertificate
    }

    $distributionPath = Write-TempJson $distributionConfig
    $distribution = Invoke-AwsJson @(
        "cloudfront", "create-distribution",
        "--distribution-config", "file://$distributionPath",
        "--query", "Distribution"
    )
    Remove-Item -LiteralPath $distributionPath -Force

    return [pscustomobject]@{
        Id = $distribution.Id
        DomainName = $distribution.DomainName
    }
}

function Set-FrontendBucketPolicy {
    param([string]$DistributionId)

    $policy = [ordered]@{
        Version = "2012-10-17"
        Statement = @(
            [ordered]@{
                Sid = "AllowCloudFrontServicePrincipalReadOnly"
                Effect = "Allow"
                Principal = [ordered]@{
                    Service = "cloudfront.amazonaws.com"
                }
                Action = "s3:GetObject"
                Resource = "arn:aws:s3:::$FrontendBucket/*"
                Condition = [ordered]@{
                    StringEquals = [ordered]@{
                        "AWS:SourceArn" = "arn:aws:cloudfront::$AccountId:distribution/$DistributionId"
                    }
                }
            }
        )
    }

    $policyPath = Write-TempJson $policy
    Invoke-AwsNoOutput @(
        "s3api", "put-bucket-policy",
        "--bucket", $FrontendBucket,
        "--policy", "file://$policyPath"
    )
    Remove-Item -LiteralPath $policyPath -Force
}

Write-Host "Phase 6E: creating/updating ALB, ECS services, S3, and CloudFront in $Region"

if ([string]::IsNullOrWhiteSpace($AccountId)) {
    $AccountId = Invoke-AwsText @("sts", "get-caller-identity", "--query", "Account")
}

if ([string]::IsNullOrWhiteSpace($VpcId)) {
    $VpcId = Invoke-AwsText @(
        "ec2", "describe-vpcs",
        "--filters", "Name=isDefault,Values=true",
        "--query", "Vpcs[0].VpcId"
    )
}

if (Test-Missing $VpcId) {
    throw "Could not find a default VPC. Re-run with -VpcId and -SubnetIds."
}

if ($SubnetIds.Count -lt 2) {
    $subnetText = Invoke-AwsText @(
        "ec2", "describe-subnets",
        "--filters", "Name=vpc-id,Values=$VpcId", "Name=default-for-az,Values=true",
        "--query", "Subnets[].SubnetId"
    )
    $SubnetIds = @($subnetText -split "\s+" | Where-Object { -not (Test-Missing $_) })
}

if ($SubnetIds.Count -lt 2) {
    $subnetText = Invoke-AwsText @(
        "ec2", "describe-subnets",
        "--filters", "Name=vpc-id,Values=$VpcId",
        "--query", "Subnets[].SubnetId"
    )
    $SubnetIds = @($subnetText -split "\s+" | Where-Object { -not (Test-Missing $_) })
}

if ($SubnetIds.Count -lt 2) {
    throw "ALB requires at least two subnets. Re-run with -SubnetIds subnet-a,subnet-b."
}

Write-Host "Account: $AccountId"
Write-Host "VPC: $VpcId"
Write-Host "Subnets: $($SubnetIds -join ', ')"

$AlbSecurityGroupId = Ensure-SecurityGroup -GroupName $AlbSecurityGroupName -Description "Allow internet HTTP/HTTPS to SLT Billing ALB"
$EcsSecurityGroupId = Ensure-SecurityGroup -GroupName $EcsSecurityGroupName -Description "Allow ALB to reach SLT Billing ECS tasks"

Add-IngressFromCidr -GroupId $AlbSecurityGroupId -Port 80 -Cidr "0.0.0.0/0"
Add-IngressFromSecurityGroup -GroupId $EcsSecurityGroupId -Port 8000 -SourceGroupId $AlbSecurityGroupId

try {
    $rdsSecurityGroupsText = Invoke-AwsText @(
        "rds", "describe-db-instances",
        "--db-instance-identifier", $RdsIdentifier,
        "--query", "DBInstances[0].VpcSecurityGroups[].VpcSecurityGroupId"
    )
    $rdsSecurityGroups = @($rdsSecurityGroupsText -split "\s+" | Where-Object { -not (Test-Missing $_) })
    foreach ($securityGroupId in $rdsSecurityGroups) {
        Write-Host "Allowing ECS tasks to reach RDS security group $securityGroupId on 5432"
        Add-IngressFromSecurityGroup -GroupId $securityGroupId -Port 5432 -SourceGroupId $EcsSecurityGroupId
    }
}
catch {
    Write-Warning "Could not update RDS security group automatically. Check RDS inbound PostgreSQL 5432 from $EcsSecurityGroupId."
}

try {
    $redisCacheClusterId = Resolve-RedisCacheClusterId
    $redisSecurityGroupsText = Invoke-AwsText @(
        "elasticache", "describe-cache-clusters",
        "--cache-cluster-id", $redisCacheClusterId,
        "--show-cache-node-info",
        "--query", "CacheClusters[0].SecurityGroups[].SecurityGroupId"
    )
    $redisSecurityGroups = @($redisSecurityGroupsText -split "\s+" | Where-Object { -not (Test-Missing $_) })
    foreach ($securityGroupId in $redisSecurityGroups) {
        Write-Host "Allowing ECS tasks to reach Redis security group $securityGroupId on 6379"
        Add-IngressFromSecurityGroup -GroupId $securityGroupId -Port 6379 -SourceGroupId $EcsSecurityGroupId
    }
}
catch {
    Write-Warning "Could not update Redis security group automatically. Check Redis inbound TCP 6379 from $EcsSecurityGroupId."
}

$loadBalancer = Ensure-LoadBalancer
$LoadBalancerArn = $loadBalancer.LoadBalancerArn
$AlbDnsName = $loadBalancer.DNSName

$targetGroup = Ensure-TargetGroup
$TargetGroupArn = $targetGroup.TargetGroupArn

Ensure-HttpListener -LoadBalancerArn $LoadBalancerArn -TargetGroupArn $TargetGroupArn
Ensure-HttpsListener -LoadBalancerArn $LoadBalancerArn -TargetGroupArn $TargetGroupArn -AcmCertificateArn $CertificateArn

if ([string]::IsNullOrWhiteSpace($BackendTaskDefinitionFile)) {
    $BackendTaskDefinitionFile = Join-Path $PSScriptRoot "task-def-backend.json"
}
if ([string]::IsNullOrWhiteSpace($WorkerTaskDefinitionFile)) {
    $WorkerTaskDefinitionFile = Join-Path $PSScriptRoot "task-def-worker.json"
}
if ([string]::IsNullOrWhiteSpace($BeatTaskDefinitionFile)) {
    $BeatTaskDefinitionFile = Join-Path $PSScriptRoot "task-def-beat.json"
}

$BackendTaskDefinition = Register-TaskDefinitionFile -Path $BackendTaskDefinitionFile
$WorkerTaskDefinition = Register-TaskDefinitionFile -Path $WorkerTaskDefinitionFile
$BeatTaskDefinition = Register-TaskDefinitionFile -Path $BeatTaskDefinitionFile

Ensure-EcsService -ServiceName $BackendServiceName -TaskDefinition $BackendTaskDefinition -DesiredCount $BackendDesiredCount -AttachLoadBalancer
Ensure-EcsService -ServiceName $WorkerServiceName -TaskDefinition $WorkerTaskDefinition -DesiredCount $WorkerDesiredCount
Ensure-EcsService -ServiceName $BeatServiceName -TaskDefinition $BeatTaskDefinition -DesiredCount $BeatDesiredCount

Ensure-FrontendBucket
$oacId = Ensure-OriginAccessControl
$functionArn = Ensure-CloudFrontFunction
$distribution = Ensure-CloudFrontDistribution -AlbDnsName $AlbDnsName -OacId $oacId -FunctionArn $functionArn
Set-FrontendBucketPolicy -DistributionId $distribution.Id

$publicBaseUrl = "https://$($distribution.DomainName)"
if (-not (Test-Missing $DomainName)) {
    $publicBaseUrl = "https://$DomainName"
}

Write-Host ""
Write-Host "Phase 6E resources are ready or updating."
Write-Host "ALB_DNS_NAME=http://$AlbDnsName"
Write-Host "FRONTEND_BUCKET=$FrontendBucket"
Write-Host "CLOUDFRONT_DISTRIBUTION_ID=$($distribution.Id)"
Write-Host "VITE_API_BASE_URL=$publicBaseUrl"
Write-Host ""
Write-Host "Add these GitHub repository secrets next:"
Write-Host "FRONTEND_BUCKET=$FrontendBucket"
Write-Host "CLOUDFRONT_DISTRIBUTION_ID=$($distribution.Id)"
Write-Host "VITE_API_BASE_URL=$publicBaseUrl"
Write-Host ""
Write-Host "CloudFront can take 10-20 minutes to finish deploying."
