import { ActionFunctionArgs, json } from "@remix-run/server-runtime";
import { getSession, destroySession } from "~/session.server";


export const action = async ({ context, request }: ActionFunctionArgs) => {
  switch (request.method) {
    case "DELETE": {
      const session = await getSession(request.headers.get("Cookie"))

      const refreshToken = session.get("refreshToken")
      if (refreshToken) {
        fetch(context.IDENTITY_SERVER_LOGOUT_ROUTE, {
          method: "DELETE",
          headers: {
            "authorization": `Bearer ${refreshToken}`
          }
        })
      }

      return json("/", {
        headers: {
          "Set-Cookie": await destroySession(session),
        }
      })
    }
    default:
      throw new Response(JSON.stringify({}), { status: 405 })
  }
} 
