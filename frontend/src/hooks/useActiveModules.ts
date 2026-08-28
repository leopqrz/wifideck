import { useCallback, useEffect, useState } from "react";
import {
  getScope,
  getAudit,
  getActive,
  type ScopeTarget,
  type AuditEntry,
} from "../api/client";

// Scope allowlist + audit log + whether active modules are enabled.
export function useActiveModules(intervalMs = 5000) {
  const [enabled, setEnabled] = useState(false);
  const [scope, setScope] = useState<ScopeTarget[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);

  const refresh = useCallback(async () => {
    try {
      const [a, s, au] = await Promise.all([getActive(), getScope(), getAudit()]);
      setEnabled(a.enabled);
      setScope(s);
      setAudit(au);
    } catch {
      /* keep prior */
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs]);

  return { enabled, scope, audit, refresh };
}
