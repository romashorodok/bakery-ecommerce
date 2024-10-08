import { useFetcher, useLoaderData, json, useOutletContext } from "@remix-run/react"
import { ActionFunctionArgs, LoaderFunctionArgs, redirect } from "@remix-run/server-runtime"
import { useEffect } from "react"
import { AppContext } from "~/root"
import { commitSession, getSession } from "~/session.server"
import { z } from 'zod';
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Button } from "~/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "~/components/ui/form"
import { Input } from "~/components/ui/input"

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))

  if (session.has("refreshToken")) {
    return redirect("/")
  }

  const result: { errors?: any } = {}

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

export const action = async ({ context: { cloudflare }, request }: ActionFunctionArgs) => {
  const session = await getSession(request.headers.get("Cookie"))
  const form = await request.formData()
  const email = form.get("email")
  const password = form.get("password")

  const response = await fetch(`${cloudflare.env.IDENTITY_SERVER_LOGIN_ROUTE}`, {
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

const formSchema = z.object({
  email: z.string().email(),
  password: z.string().min(4).max(32),
})

export default function Login() {
  const fetcher = useFetcher<typeof action>()
  const { errors } = useLoaderData<typeof loader>()

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
  })

  const { setAccessToken } = useOutletContext<AppContext>()

  function onSubmit(values: z.infer<typeof formSchema>) {
    fetcher.submit(values, {
      method: 'POST',
    })
  }

  useEffect(() => {
    if (fetcher.data?.access_token) {
      const accessToken = fetcher.data.access_token
      setAccessToken(accessToken)
    }
  }, [setAccessToken, fetcher.data])

  return (
    <>
      {errors && <h1>Login has error {JSON.stringify(errors)}</h1>}
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="email" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>password</FormLabel>
                <FormControl>
                  <Input placeholder="password" type="password" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit">Submit</Button>
        </form>
      </Form>

    </>
  )
}
