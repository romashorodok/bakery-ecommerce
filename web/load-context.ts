import { type AppLoadContext } from "@remix-run/cloudflare";
import { type PlatformProxy } from "wrangler";

type Cloudflare = Omit<PlatformProxy<Env>, "dispose">;

declare module "@remix-run/cloudflare" {
  interface AppLoadContext {
    cloudflare: Cloudflare,
    IDENTITY_SERVER_LOGIN_ROUTE: string,
    IDENTITY_SERVER_REFRESH_TOKEN_ROUTE: string,
    IDENTITY_SERVER_LOGOUT_ROUTE: string,
  }
}

type GetLoadContext = (args: {
  request: Request;
  context: { cloudflare: Cloudflare }; // load context _before_ augmentation
}) => AppLoadContext;

export const getLoadContext: GetLoadContext = ({
  context,
}) => {
  return {
    IDENTITY_SERVER_LOGIN_ROUTE: "http://localhost:9000/api/identity/login",
    IDENTITY_SERVER_REFRESH_TOKEN_ROUTE: "http://localhost:9000/api/identity/refresh-access-token",
    IDENTITY_SERVER_LOGOUT_ROUTE: "http://localhost:9000/api/identity",
    ...context,
  };
};
