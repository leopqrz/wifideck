import { useEffect, useState } from "react";
import { getSchedule, runJob, updateJob, type Job } from "../api/client";

// Interval jobs (rescan, WIDS sweep, heartbeat) — toggle on/off, set the interval,
// or run one now. All off by default.
export function SchedulePanel() {
  const [jobs, setJobs] = useState<Job[]>([]);

  const load = () =>
    getSchedule()
      .then(setJobs)
      .catch(() => {
        /* leave last list */
      });

  useEffect(() => {
    load();
    const t = window.setInterval(load, 5000);
    return () => window.clearInterval(t);
  }, []);

  async function toggle(j: Job) {
    await updateJob(j.id, { enabled: !j.enabled }).catch(() => {});
    load();
  }
  async function changeInterval(j: Job, v: string) {
    const n = Number(v);
    if (n && n !== j.interval_sec) {
      await updateJob(j.id, { interval_sec: n }).catch(() => {});
      load();
    }
  }
  async function run(j: Job) {
    await runJob(j.id).catch(() => {});
    load();
  }

  return (
    <div className="rounded-[10px] border border-line bg-panel p-5">
      <span className="font-mono text-[10px] uppercase tracking-hud text-faint">Scheduler</span>
      <p className="mt-2 font-mono text-[11px] text-muted">
        Run tasks on an interval — rescan, WIDS sweep, heartbeat. Off by default.
      </p>
      <div className="mt-3 flex flex-col gap-2">
        {jobs.length === 0 && <span className="font-mono text-[11px] text-faint">no jobs</span>}
        {jobs.map((j) => (
          <div
            key={j.id}
            className="flex flex-wrap items-center gap-3 rounded border border-line-soft bg-panel-2 px-3 py-2"
          >
            <button
              onClick={() => toggle(j)}
              className={`rounded border px-2 py-0.5 font-mono text-[11px] ${
                j.enabled ? "border-ok/40 text-ok" : "border-line text-faint"
              }`}
            >
              {j.enabled ? "on" : "off"}
            </button>
            <span className="font-mono text-xs text-text">{j.label}</span>
            <label className="flex items-center gap-1 font-mono text-[10px] text-faint">
              every
              <input
                inputMode="numeric"
                defaultValue={j.interval_sec}
                onBlur={(e) => changeInterval(j, e.target.value.replace(/\D/g, ""))}
                className="w-16 rounded border border-line bg-panel px-1.5 py-0.5 font-mono text-xs text-text outline-none focus:border-accent"
              />
              s
            </label>
            <button
              onClick={() => run(j)}
              className="rounded border border-line px-2 py-0.5 font-mono text-[11px] text-text hover:border-accent"
            >
              Run now
            </button>
            <span className="ml-auto font-mono text-[10px] text-muted">
              {j.runs > 0 ? `${j.runs} runs · ${j.last_result ?? ""}` : "never run"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
