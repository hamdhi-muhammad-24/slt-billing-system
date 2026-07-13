"""Statistics tracker."""
import time
import json
import os
from datetime import datetime
from collections import defaultdict


class StatsTracker:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = []
        self.by_template = defaultdict(lambda: {"success": 0, "failed": 0, "durations": []})

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()

    def add_result(self, result):
        self.results.append(result)
        template = result.template_id or "unknown"
        if result.success:
            self.by_template[template]["success"] += 1
        else:
            self.by_template[template]["failed"] += 1
        self.by_template[template]["durations"].append(result.duration)

    def total_duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def summary(self):
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        duration = self.total_duration()
        rate_per_sec = total / duration if duration > 0 else 0

        template_stats = {}
        for template, stats in self.by_template.items():
            durations = stats["durations"]
            avg_ms = (sum(durations) / len(durations) * 1000) if durations else 0
            template_stats[template] = {
                "total": stats["success"] + stats["failed"],
                "success": stats["success"],
                "failed": stats["failed"],
                "avg_duration_ms": round(avg_ms, 2),
            }

        return {
            "total_files": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round((successful / total * 100), 2) if total > 0 else 0,
            "total_duration_seconds": round(duration, 2),
            "rate_per_second": round(rate_per_sec, 2),
            "rate_per_hour": round(rate_per_sec * 3600, 0),
            "target_per_hour": 40000,
            "target_met": (rate_per_sec * 3600) >= 40000,
            "by_template": template_stats,
        }

    def save_report(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f"stats_{timestamp}.json")

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.summary(),
            "failed_files": [
                {"source": r.source_file, "error": r.error}
                for r in self.results if not r.success
            ],
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        return report_path

    def print_summary(self, log_callback=None):
        log = log_callback or print
        s = self.summary()

        log("\n" + "=" * 70)
        log("PROCESSING SUMMARY")
        log("=" * 70)
        log(f"Total files:      {s['total_files']}")
        log(f"Successful:       {s['successful']}")
        log(f"Failed:           {s['failed']}")
        log(f"Success rate:     {s['success_rate']}%")
        log(f"Total duration:   {s['total_duration_seconds']}s")
        log(f"Rate:             {s['rate_per_second']} files/sec")
        log(f"                  {s['rate_per_hour']:,.0f} files/hour")
        log(f"Target:           {s['target_per_hour']:,} files/hour")
        log(f"Target met:       {'YES' if s['target_met'] else 'NO'}")

        if s['by_template']:
            log("\nBy template:")
            for template, stats in s['by_template'].items():
                log(f"  {template}: {stats['success']}/{stats['total']} "
                    f"(avg {stats['avg_duration_ms']}ms)")
        log("=" * 70 + "\n")