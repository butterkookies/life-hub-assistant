import { useEffect, useState } from 'react';

import {
  ensureServerReady,
  getServerStatus,
  ServerStatus,
  subscribeServerStatus,
} from '../lib/api';

export function useServerStatus() {
  const [status, setStatus] = useState<ServerStatus>(getServerStatus());

  useEffect(() => subscribeServerStatus(setStatus), []);

  return {
    status,
    retry: () => ensureServerReady(true),
  };
}
