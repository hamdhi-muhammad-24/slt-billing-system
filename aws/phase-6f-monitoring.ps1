[CmdletBinding()]
param(
    [string]$Region = "ap-southeast-1",
    [string]$ClusterName = "slt-cluster",
    [string]$BackendServiceName = "slt-backend-service",
    [string]$WorkerServiceName = "slt-worker-service",
    [string]$BeatServiceName = "slt-beat-service",
    [string]$AlbName = "slt-billing-alb",
    [string]$TargetGroupName = "slt-backend-tg",
    [string]$RdsIdentifier = "slt-billing-db",
    [string]$RedisClusterId = "slt-redis",
    [string]$DashboardName = "slt-billing-production",
    [string]$AlertEmail = "",
    [int]$EcsCpuThreshold = 80,
    [int]$EcsMemoryThreshold = 80,
    [int]$RdsCpuThreshold = 80,
    [int]$RdsMaxConnections = 80,
    [Int64]$RdsMinFreeStorageBytes = 2147483648,
    [int]$RedisCpuThreshold = 80,
    [int]$RedisMemoryThreshold = 80,
    [int]$RedisMaxConnections = 100
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

function Invoke-AwsNoOutput {
    param([object[]]$AwsArgs)

    $output = & aws @AwsArgs --region $Region 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "aws $($AwsArgs -join ' ') failed: $($output | Out-String)"
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

function Put-MetricAlarm {
    param([object[]]$AlarmArgs)

    $args = @("cloudwatch", "put-metric-alarm") + $AlarmArgs
    if ($AlarmActions.Count -gt 0) {
        $args += @("--alarm-actions") + $AlarmActions
    }

    Invoke-AwsNoOutput $args
}

function Add-EcsAlarms {
    param([string]$ServiceName)

    Put-MetricAlarm @(
        "--alarm-name", "$ServiceName-cpu-high",
        "--alarm-description", "ECS CPU is high for $ServiceName",
        "--namespace", "AWS/ECS",
        "--metric-name", "CPUUtilization",
        "--dimensions", "Name=ClusterName,Value=$ClusterName", "Name=ServiceName,Value=$ServiceName",
        "--statistic", "Average",
        "--period", "300",
        "--evaluation-periods", "2",
        "--threshold", $EcsCpuThreshold,
        "--comparison-operator", "GreaterThanThreshold",
        "--treat-missing-data", "notBreaching"
    )

    Put-MetricAlarm @(
        "--alarm-name", "$ServiceName-memory-high",
        "--alarm-description", "ECS memory is high for $ServiceName",
        "--namespace", "AWS/ECS",
        "--metric-name", "MemoryUtilization",
        "--dimensions", "Name=ClusterName,Value=$ClusterName", "Name=ServiceName,Value=$ServiceName",
        "--statistic", "Average",
        "--period", "300",
        "--evaluation-periods", "2",
        "--threshold", $EcsMemoryThreshold,
        "--comparison-operator", "GreaterThanThreshold",
        "--treat-missing-data", "notBreaching"
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

Write-Host "Phase 6F: creating CloudWatch alarms and dashboard in $Region"

$AlarmActions = @()
if (-not (Test-Missing $AlertEmail)) {
    $topicArn = Invoke-AwsText @("sns", "create-topic", "--name", "slt-billing-alerts", "--query", "TopicArn")
    Invoke-AwsNoOutput @(
        "sns", "subscribe",
        "--topic-arn", $topicArn,
        "--protocol", "email",
        "--notification-endpoint", $AlertEmail
    )
    $AlarmActions = @($topicArn)
    Write-Host "SNS alert topic ready. Confirm the subscription email from AWS before expecting alarm emails."
}

Add-EcsAlarms -ServiceName $BackendServiceName
Add-EcsAlarms -ServiceName $WorkerServiceName
Add-EcsAlarms -ServiceName $BeatServiceName

$loadBalancerArn = Invoke-AwsText @(
    "elbv2", "describe-load-balancers",
    "--names", $AlbName,
    "--query", "LoadBalancers[0].LoadBalancerArn"
)
$loadBalancerDimension = $loadBalancerArn -replace "^.*:loadbalancer/", ""

$targetGroupArn = Invoke-AwsText @(
    "elbv2", "describe-target-groups",
    "--names", $TargetGroupName,
    "--query", "TargetGroups[0].TargetGroupArn"
)
$targetGroupDimension = $targetGroupArn -replace "^.*:targetgroup/", "targetgroup/"

Put-MetricAlarm @(
    "--alarm-name", "slt-alb-elb-5xx-high",
    "--alarm-description", "ALB generated too many 5xx responses",
    "--namespace", "AWS/ApplicationELB",
    "--metric-name", "HTTPCode_ELB_5XX_Count",
    "--dimensions", "Name=LoadBalancer,Value=$loadBalancerDimension",
    "--statistic", "Sum",
    "--period", "300",
    "--evaluation-periods", "1",
    "--threshold", "5",
    "--comparison-operator", "GreaterThanThreshold",
    "--treat-missing-data", "notBreaching"
)

Put-MetricAlarm @(
    "--alarm-name", "slt-alb-target-5xx-high",
    "--alarm-description", "Backend targets generated too many 5xx responses",
    "--namespace", "AWS/ApplicationELB",
    "--metric-name", "HTTPCode_Target_5XX_Count",
    "--dimensions", "Name=LoadBalancer,Value=$loadBalancerDimension", "Name=TargetGroup,Value=$targetGroupDimension",
    "--statistic", "Sum",
    "--period", "300",
    "--evaluation-periods", "1",
    "--threshold", "5",
    "--comparison-operator", "GreaterThanThreshold",
    "--treat-missing-data", "notBreaching"
)

Put-MetricAlarm @(
    "--alarm-name", "slt-alb-target-response-slow",
    "--alarm-description", "Backend target response time is high",
    "--namespace", "AWS/ApplicationELB",
    "--metric-name", "TargetResponseTime",
    "--dimensions", "Name=LoadBalancer,Value=$loadBalancerDimension", "Name=TargetGroup,Value=$targetGroupDimension",
    "--statistic", "Average",
    "--period", "300",
    "--evaluation-periods", "2",
    "--threshold", "2",
    "--comparison-operator", "GreaterThanThreshold",
    "--treat-missing-data", "notBreaching"
)

Put-MetricAlarm @(
    "--alarm-name", "slt-rds-cpu-high",
    "--alarm-description", "RDS CPU is high",
    "--namespace", "AWS/RDS",
    "--metric-name", "CPUUtilization",
    "--dimensions", "Name=DBInstanceIdentifier,Value=$RdsIdentifier",
    "--statistic", "Average",
    "--period", "300",
    "--evaluation-periods", "2",
    "--threshold", $RdsCpuThreshold,
    "--comparison-operator", "GreaterThanThreshold",
    "--treat-missing-data", "notBreaching"
)

Put-MetricAlarm @(
    "--alarm-name", "slt-rds-connections-high",
    "--alarm-description", "RDS database connections are high",
    "--namespace", "AWS/RDS",
    "--metric-name", "DatabaseConnections",
    "--dimensions", "Name=DBInstanceIdentifier,Value=$RdsIdentifier",
    "--statistic", "Average",
    "--period", "300",
    "--evaluation-periods", "2",
    "--threshold", $RdsMaxConnections,
    "--comparison-operator", "GreaterThanThreshold",
    "--treat-missing-data", "notBreaching"
)

Put-MetricAlarm @(
    "--alarm-name", "slt-rds-free-storage-low",
    "--alarm-description", "RDS free storage is low",
    "--namespace", "AWS/RDS",
    "--metric-name", "FreeStorageSpace",
    "--dimensions", "Name=DBInstanceIdentifier,Value=$RdsIdentifier",
    "--statistic", "Average",
    "--period", "300",
    "--evaluation-periods", "2",
    "--threshold", $RdsMinFreeStorageBytes,
    "--comparison-operator", "LessThanThreshold",
    "--treat-missing-data", "notBreaching"
)

$redisMetricDimensions = @()
try {
    $resolvedRedisClusterId = Resolve-RedisCacheClusterId
    $cacheClusterId = Invoke-AwsText @(
        "elasticache", "describe-cache-clusters",
        "--cache-cluster-id", $resolvedRedisClusterId,
        "--show-cache-node-info",
        "--query", "CacheClusters[0].CacheClusterId"
    )
    if (-not (Test-Missing $cacheClusterId)) {
        $redisMetricDimensions = @("Name=CacheClusterId,Value=$cacheClusterId", "Name=CacheNodeId,Value=0001")
    }
}
catch {
    Write-Warning "Could not discover Redis cache cluster dimensions. Redis alarms will be skipped."
}

if ($redisMetricDimensions.Count -gt 0) {
    $redisCpuAlarmArgs = @(
        "--alarm-name", "slt-redis-cpu-high",
        "--alarm-description", "Redis CPU is high",
        "--namespace", "AWS/ElastiCache",
        "--metric-name", "CPUUtilization",
        "--dimensions"
    ) + $redisMetricDimensions + @(
        "--statistic", "Average",
        "--period", "300",
        "--evaluation-periods", "2",
        "--threshold", $RedisCpuThreshold,
        "--comparison-operator", "GreaterThanThreshold",
        "--treat-missing-data", "notBreaching"
    )
    Put-MetricAlarm $redisCpuAlarmArgs

    $redisMemoryAlarmArgs = @(
        "--alarm-name", "slt-redis-memory-high",
        "--alarm-description", "Redis memory usage is high",
        "--namespace", "AWS/ElastiCache",
        "--metric-name", "DatabaseMemoryUsagePercentage",
        "--dimensions"
    ) + $redisMetricDimensions + @(
        "--statistic", "Average",
        "--period", "300",
        "--evaluation-periods", "2",
        "--threshold", $RedisMemoryThreshold,
        "--comparison-operator", "GreaterThanThreshold",
        "--treat-missing-data", "notBreaching"
    )
    Put-MetricAlarm $redisMemoryAlarmArgs

    $redisConnectionsAlarmArgs = @(
        "--alarm-name", "slt-redis-connections-high",
        "--alarm-description", "Redis current connections are high",
        "--namespace", "AWS/ElastiCache",
        "--metric-name", "CurrConnections",
        "--dimensions"
    ) + $redisMetricDimensions + @(
        "--statistic", "Average",
        "--period", "300",
        "--evaluation-periods", "2",
        "--threshold", $RedisMaxConnections,
        "--comparison-operator", "GreaterThanThreshold",
        "--treat-missing-data", "notBreaching"
    )
    Put-MetricAlarm $redisConnectionsAlarmArgs
}

$dashboardWidgets = @(
    [ordered]@{
        type = "metric"
        width = 12
        height = 6
        properties = [ordered]@{
            title = "ECS services CPU"
            region = $Region
            view = "timeSeries"
            metrics = @(
                @("AWS/ECS", "CPUUtilization", "ClusterName", $ClusterName, "ServiceName", $BackendServiceName),
                @(".", ".", ".", ".", "ServiceName", $WorkerServiceName),
                @(".", ".", ".", ".", "ServiceName", $BeatServiceName)
            )
        }
    },
    [ordered]@{
        type = "metric"
        width = 12
        height = 6
        properties = [ordered]@{
            title = "ECS services memory"
            region = $Region
            view = "timeSeries"
            metrics = @(
                @("AWS/ECS", "MemoryUtilization", "ClusterName", $ClusterName, "ServiceName", $BackendServiceName),
                @(".", ".", ".", ".", "ServiceName", $WorkerServiceName),
                @(".", ".", ".", ".", "ServiceName", $BeatServiceName)
            )
        }
    },
    [ordered]@{
        type = "metric"
        width = 12
        height = 6
        properties = [ordered]@{
            title = "ALB errors and response time"
            region = $Region
            view = "timeSeries"
            metrics = @(
                @("AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", $loadBalancerDimension, @{ "stat" = "Sum" }),
                @(".", "HTTPCode_Target_5XX_Count", ".", $loadBalancerDimension, "TargetGroup", $targetGroupDimension, @{ "stat" = "Sum" }),
                @(".", "TargetResponseTime", ".", $loadBalancerDimension, ".", $targetGroupDimension, @{ "stat" = "Average" })
            )
        }
    },
    [ordered]@{
        type = "metric"
        width = 12
        height = 6
        properties = [ordered]@{
            title = "RDS health"
            region = $Region
            view = "timeSeries"
            metrics = @(
                @("AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", $RdsIdentifier),
                @(".", "DatabaseConnections", ".", $RdsIdentifier),
                @(".", "FreeStorageSpace", ".", $RdsIdentifier)
            )
        }
    }
)

if ($redisMetricDimensions.Count -gt 0) {
    $dashboardWidgets += [ordered]@{
        type = "metric"
        width = 12
        height = 6
        properties = [ordered]@{
            title = "Redis health"
            region = $Region
            view = "timeSeries"
            metrics = @(
                @("AWS/ElastiCache", "CPUUtilization", "CacheClusterId", $cacheClusterId, "CacheNodeId", "0001"),
                @(".", "DatabaseMemoryUsagePercentage", ".", $cacheClusterId, ".", "0001"),
                @(".", "CurrConnections", ".", $cacheClusterId, ".", "0001")
            )
        }
    }
}

$dashboard = [ordered]@{ widgets = $dashboardWidgets }
$dashboardPath = Write-TempJson $dashboard
Invoke-AwsNoOutput @(
    "cloudwatch", "put-dashboard",
    "--dashboard-name", $DashboardName,
    "--dashboard-body", "file://$dashboardPath"
)
Remove-Item -LiteralPath $dashboardPath -Force

Write-Host "Phase 6F monitoring is ready."
Write-Host "Dashboard: $DashboardName"
if ($AlarmActions.Count -gt 0) {
    Write-Host "Alarm email: $AlertEmail"
    Write-Host "Manual step: open your email and confirm the AWS SNS subscription."
}
