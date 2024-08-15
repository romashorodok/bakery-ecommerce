// Generated by Wrangler on Thu Aug 15 2024 22:40:31 GMT+0300 (Eastern European Summer Time)
// by running `wrangler types`

interface Env {
	IDENTITY_SERVER_LOGIN_ROUTE: "http://localhost:9000/api/identity/login";
	IDENTITY_SERVER_REFRESH_TOKEN_ROUTE: "http://localhost:9000/api/identity/refresh-access-token";
	IDENTITY_SERVER_LOGOUT_ROUTE: "http://localhost:9000/api/identity";
	PRODUCTS_ROUTE: "http://localhost:9000/api/products";
	CATALOGS_ROUTE: "http://localhost:9000/api/catalogs";
	FRONT_PAGE_ROUTE: "http://localhost:9000/api/front-page";
	CART_ROUTE: "http://localhost:9000/api/carts";
	PAYMENT_ROUTE: "http://localhost:9000/api/payments";
	STRIPE_PUBLIC_KEY: string;
}
