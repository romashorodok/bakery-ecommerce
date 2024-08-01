import { useOutletContext } from "@remix-run/react";
import { useCallback } from "react";
import { AppContext } from "~/root";

class Mutex {
  wait: Promise<void>;
  private _locks: number;

  constructor() {
    this.wait = Promise.resolve();
    this._locks = 0;
  }

  isLocked() {
    return this._locks > 0;
  }

  lock() {
    this._locks += 1;
    let unlockNext: () => void;
    const willLock = new Promise<void>(
      (resolve) =>
      (unlockNext = () => {
        this._locks -= 1;
        resolve();
      }),
    );
    const willUnlock = this.wait.then(() => unlockNext);
    this.wait = this.wait.then(() => willLock);
    return willUnlock;
  }
}

type useAuthRequestInit = RequestInit & {}

const useAuthFetchRequestMutex = new Mutex()

export function useAuthFetch() {
  const { accessToken, setAccessToken } = useOutletContext<AppContext>()

  const __fetch = useCallback(async (url: string, init?: useAuthRequestInit) => {
    if (!accessToken || !setAccessToken) {
      throw Error(`Missing access token for auth ${url} route`)
    }

    if (!init) {
      init = { headers: {} }
    }

    if (!init.headers) {
      init.headers = {}
    }

    // @ts-ignore
    init.headers['authorization'] = `Bearer ${accessToken}`

    if (useAuthFetchRequestMutex.isLocked()) {
      console.warn(`Trying send authorized by unauthorized identity request url: ${url} , init: ${init}`)
      return
    }

    const unlock = await useAuthFetchRequestMutex.lock()

    try {
      const resp = await fetch(url, init).catch()

      switch (resp.status) {
        case 401:
          setAccessToken(undefined)
        case 403:
          await fetch("/session_refresh_access_token", {
            method: "POST"
          })
            .then(r => r.json<{ access_token: string }>())
            .then(r => setAccessToken(r.access_token))
            .catch(() => {
              setAccessToken(undefined)
              fetch("/session_delete", {
                method: "DELETE"
              })
            })
      }

      return resp
    } finally {
      unlock()
    }

  }, [accessToken])

  return { fetch: __fetch }
}
