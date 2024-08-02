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
      console.warn(`Trying send authorized by unauthorized identity request url: ${url} , init: ${JSON.stringify(init)}`)
      return
    }

    const unlock = await useAuthFetchRequestMutex.lock()

    try {
      const resp = await fetch(url, init).catch()

      switch (resp.status) {
        case 401:
          setAccessToken(undefined)
        case 403:
          const response = await fetch("/session_refresh_access_token", {
            method: "POST"
          }).catch()

          if (response.status !== 200 && response.status !== 201) {
            console.log("Unable refresh access token")
            await fetch("/session_delete", {
              method: "DELETE"
            })
            setAccessToken(undefined)
            return resp
          }

          const data = await response.json<{ access_token: string }>()
          if (!data.access_token) {
            console.log("Not found access token after refresh")
            setAccessToken(undefined)
            return resp
          }


          // @ts-ignore
          init.headers['authorization'] = `Bearer ${data.access_token}`
          const newResp = await fetch(url, init).catch()
          setAccessToken(data.access_token)
          return newResp
      }

      return resp
    } finally {
      unlock()
    }
  }, [accessToken])

  return { fetch: __fetch, accessToken }
}
