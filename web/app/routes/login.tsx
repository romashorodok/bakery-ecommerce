import { useFetcher, useLoaderData, json, useActionData, useNavigate, Form, useOutletContext } from "@remix-run/react"
import { ActionFunctionArgs, LoaderFunctionArgs, redirect } from "@remix-run/server-runtime"
import { Dispatch, SetStateAction, useContext, useEffect } from "react"
import { AccessTokenContext } from "~/root"
import { commitSession, getSession } from "~/session.server"

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))

  if (session.has("refreshToken")) {
    return redirect("/")
  }

  const result: { errors?: any, login: string } = { login: "test" }

  const errorDetail = session.get("error")

  if (errorDetail) {
    result.errors = errorDetail
  }

  return json(result, {
    headers: {
      'Set-Cookie': await commitSession(session)
    }
  })
}

export const action = async ({ context, request }: ActionFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))
  const form = await request.formData()
  const email = form.get("email")
  const password = form.get("password")

  const response = await fetch(`${context.IDENTITY_SERVER_LOGIN_ROUTE}`, {
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
    body: JSON.stringify({
      email,
      password,
    })
  })

  if (response.status !== 200 && response.status !== 201) {
    const msg = await response.json<any>()
    session.flash("error", msg)
    return redirect("/login", {
      headers: {
        "Set-Cookie": await commitSession(session),
      },
      status: response.status,
    })
  }

  const result = await response.json<{ refresh_token: { value: string, expires_at: number }, access_token: { value: string, expires_at: number } }>()

  session.set('refreshToken', result.refresh_token.value)
  session.set('accessToken', result.access_token.value)

  return json({ access_token: result.access_token.value }, {
    headers: {
      "Set-Cookie": await commitSession(session),
    }
  })
}

export default function Login() {
  const fetcher = useFetcher<typeof action>()
  const { errors } = useLoaderData<typeof loader>()

  const { setAccessToken } = useOutletContext<{ setAccessToken: Dispatch<SetStateAction<string | undefined>> }>()

  useEffect(() => {
    if (fetcher.data?.access_token) {
      const accessToken = fetcher.data.access_token
      console.log("result", accessToken)
      setAccessToken(accessToken)
    }
  }, [setAccessToken, fetcher.data])

  return (
    <>
      {errors && <h1>Login has error {JSON.stringify(errors)}</h1>}

      <div>Hello world</div>

      <fetcher.Form method="POST">
        <input type="email" name="email"></input>
        <input type="password" name="password"></input>

        <button>Log In!</button>
      </fetcher.Form>
    </>
  )
}
