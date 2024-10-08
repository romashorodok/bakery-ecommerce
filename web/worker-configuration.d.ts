// Generated by Wrangler on Fri Aug 23 2024 01:06:46 GMT+0300 (Eastern European Summer Time)
// by running `wrangler types`

interface Env {
	IDENTITY_SERVER_LOGIN_ROUTE: "http://localhost:9000/api/identity/login";
	IDENTITY_SERVER_REFRESH_TOKEN_ROUTE: "http://localhost:9000/api/identity/refresh-access-token";
	IDENTITY_SERVER_LOGOUT_ROUTE: "http://localhost:9000/api/identity";
	OBJECT_STORE_ROUTE: "http://localhost:9001";
	PRODUCTS_ROUTE: "http://localhost:9000/api/products";
	CATALOGS_ROUTE: "http://localhost:9000/api/catalogs";
	FRONT_PAGE_ROUTE: "http://localhost:9000/api/front-page";
	CART_ROUTE: "http://localhost:9000/api/carts";
	PAYMENT_ROUTE: "http://localhost:9000/api/payments";
	ORDER_ROUTE: "http://localhost:9000/api/orders";
	IMAGE_ROUTE: "http://localhost:9000/api/images";
	STRIPE_PUBLIC_KEY: string;
}
