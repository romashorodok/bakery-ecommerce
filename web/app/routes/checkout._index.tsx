import { useLoaderData, useNavigate } from '@remix-run/react';
import { LoaderFunctionArgs, json } from '@remix-run/cloudflare';
import { loadStripe } from '@stripe/stripe-js';
import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthFetch } from '~/hooks/useAuthFetch';

import { Label } from "~/components/ui/label"
import { RadioGroup, RadioGroupItem } from "~/components/ui/radio-group"
import { AspectRatio } from "~/components/ui/aspect-ratio"
import {
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "~/components/ui/table"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { Elements } from "@stripe/react-stripe-js";
import {
  PaymentElement,
  useStripe,
  useElements
} from "@stripe/react-stripe-js";

export const loader = async ({ context: { cloudflare: { env } } }: LoaderFunctionArgs) => {
  return json({
    stripePubkey: env.STRIPE_PUBLIC_KEY,
    paymentRoute: env.PAYMENT_ROUTE,
    orderRoute: env.ORDER_ROUTE,
    objectStoreRoute: env.OBJECT_STORE_ROUTE,
  })
}

function StripeCheckoutForm() {
  const stripe = useStripe();
  const elements = useElements();

  const [message, setMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate()

  useEffect(() => {
    if (!stripe) {
      return;
    }

    const clientSecret = new URLSearchParams(window.location.search).get(
      "payment_intent_client_secret"
    );

    if (!clientSecret) {
      return;
    }

    stripe.retrievePaymentIntent(clientSecret).then(({ paymentIntent }) => {
      if (!paymentIntent) return

      switch (paymentIntent.status) {
        case "succeeded":
          setMessage("Payment succeeded!");
          break;
        case "processing":
          setMessage("Your payment is processing.");
          break;
        case "requires_payment_method":
          setMessage("Your payment was not successful, please try again.");
          break;
        default:
          setMessage("Something went wrong.");
          break;
      }
    });
  }, [stripe]);

  const handleSubmit = async (e: any) => {
    e.preventDefault();

    if (!stripe || !elements) {
      // Stripe.js hasn't yet loaded.
      // Make sure to disable form submission until Stripe.js has loaded.
      return
    }

    setIsLoading(true);

    const { error } = await stripe.confirmPayment({
      elements,
      redirect: 'if_required',
    });

    // This point will only be reached if there is an immediate error when
    // confirming the payment. Otherwise, your customer will be redirected to
    // your `return_url`. For some payment methods like iDEAL, your customer will
    // be redirected to an intermediate site first to authorize the payment, then
    // redirected to the `return_url`.
    if (error && (error.type === "card_error" || error.type === "validation_error")) {
      setMessage(error.message || null);
    } else {
      setMessage("An unexpected error occurred.");
    }

    setIsLoading(false);
    navigate("/orders")
  };

  return (
    <form id="payment-form" onSubmit={handleSubmit}>

      <PaymentElement id="payment-element" options={{ layout: 'tabs' }} />
      <button disabled={isLoading || !stripe || !elements} id="submit">
        <span id="button-text">
          {isLoading ? <div className="spinner" id="spinner"></div> : "Pay now"}
        </span>
      </button>
      {/* Show any error or success messages */}
      {message && <div id="payment-message">{message}</div>}
    </form>
  );
}

function useStripeSession({ paymentRoute }: { paymentRoute: string }) {
  const { fetch } = useAuthFetch()

  const model = useQuery({
    queryKey: ["stripe-client-secret"],
    queryFn: async () => {
      const response = await fetch(`${paymentRoute}/stripe/payment-intent`, {
        method: "POST",
      })
      if (!response || !response.ok)
        throw new Error("Something goes wrong at stripe payment intent...")
      return response.json<{ client_secret: string }>()
    }
  })

  return { model }
}

function StripeSession({ paymentRoute, stripePubkey }: { stripePubkey: string, paymentRoute: string }) {
  const { model } = useStripeSession({ paymentRoute })

  const stripe = useMemo(() => loadStripe(stripePubkey), [stripePubkey])

  return (
    <div>
      {model.data?.client_secret && (
        <Elements options={{
          clientSecret: model.data.client_secret,
          appearance: { theme: 'stripe' },
        }} stripe={stripe} >
          <StripeCheckoutForm />
        </Elements>
      )}
    </div>
  )
}


const PAYMENT_PROVIDER = {
  STRIPE: "STRIPE",
  PAYPAL: "PAYPAL"
} as const

type PAYMENT_PROVIDER_KEY = keyof typeof PAYMENT_PROVIDER

type PaymentDetail = {
  id: string,
  payment_provider: PAYMENT_PROVIDER_KEY
}

type Image = { bucket: string, original_file: string, transcoded_file_mime: string, original_file_hash: string, transcoded_file: string, id: string }
type ProductImage = { product_id: string, image_id: string, featured: boolean, id: string, image: Image }
type Product = { id: string, name: string, price: number, product_images: Array<ProductImage> }

type OrderItem = {
  order_id: string,
  product_id: string,
  quantity: number,
  id: string,
  price: number,
  price_multiplied: number,
  price_multiplier: number,
  product: Product,
}

type Order = {
  id: string,
  payment_detail_id: string,
  user_id: string,
  order_status: string,
  payment_detail: PaymentDetail,
  order_items: Array<OrderItem>
}

function OrderItemView({ id, quantity, price, objectStoreRoute, product: { name, product_images } }: OrderItem & { objectStoreRoute: string }) {
  const featuredImage = product_images.find(image => image.featured);

  return (
    <Card key={id} className="w-[400px]">
      <CardHeader className="cursor-pointer">
        <CardTitle>{name}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableBody>
            <TableRow className="flex place-items-center hover:bg-transparent focus:outline-none">
              <TableCell className="flex-[1]">
                <AspectRatio ratio={16 / 9} className="bg-muted">
                  {featuredImage ?
                    <img src={`${objectStoreRoute}/${featuredImage.image.bucket}/${featuredImage?.image.transcoded_file || featuredImage?.image.original_file}`} className="rounded-md object-cover w-full h-full" />
                    : null
                  }
                </AspectRatio>
              </TableCell>
              <TableCell className="flex-[1] sm:table-cell">
                <div className="flex gap-1 justify-end font-semibold">
                  <h1>{quantity}</h1>
                  <h1>x</h1>
                  <h1>${price}</h1>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

const ORDER_DRAFT_SESSION = "order-draft-session"
const ORDER_DRAFT_CART_CONVERSATION = "order-draft-cart-conversation-to-order"
const ORDER_DRAFT_PAYMENT_METHOD = "order-draft-payment-method"


function useOrderSession({ orderRoute }: { orderRoute: string }) {
  const { fetch } = useAuthFetch()
  const client = useQueryClient()

  const model = useQuery({
    queryKey: [ORDER_DRAFT_SESSION],
    queryFn: async () => {
      const response = await fetch(`${orderRoute}/draft`, {
        method: "GET",
      })
      if (!response || !response.ok) {
        throw new Error('Something goes wrong...')
      }
      return await response.json<{ order: Order }>()
    }
  })

  const cartConversationToOrder = useMutation({
    mutationKey: [ORDER_DRAFT_CART_CONVERSATION],
    mutationFn: async () => {
      const response = await fetch(`${orderRoute}/draft/convert-cart-to-order`, {
        method: "PUT",
        headers: {
          "content-type": "application/json",
        },
      })
      if (!response || !response.ok) {
        throw new Error('Something goes wrong at cart conversation...')
      }
      return response.json()
    },
    onSuccess: () => client.invalidateQueries({ queryKey: [ORDER_DRAFT_SESSION] }),
  })

  const mutatePaymentMethod = useMutation({
    mutationKey: [ORDER_DRAFT_PAYMENT_METHOD],
    mutationFn: async (provider: PAYMENT_PROVIDER_KEY) => {
      const response = await fetch(`${orderRoute}/draft/payment-method`, {
        method: "PUT",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({ provider })
      })
      if (!response || !response.ok) {
        throw new Error('Something goes wrong...')
      }
      return response.json<{ payment_detail: string }>()
    },
  })

  return { model, mutatePaymentMethod, cartConversationToOrder }
}

export default function CheckoutIndex() {
  const { stripePubkey, paymentRoute, orderRoute, objectStoreRoute } = useLoaderData<typeof loader>()

  const { model, mutatePaymentMethod, cartConversationToOrder } = useOrderSession({ orderRoute })

  const [provider, setProvider] = useState<PAYMENT_PROVIDER_KEY | undefined>()

  useEffect(() => {
    if (!mutatePaymentMethod.data?.payment_detail) return
    cartConversationToOrder.mutate()
  }, [mutatePaymentMethod.data])

  useEffect(() => {
    if (!provider) return
    mutatePaymentMethod.mutate(provider)
  }, [provider])

  if (model.isLoading) {
    return (
      <div>
        <h1>Loading...</h1>
      </div>
    )
  }

  if (model.data?.order) {
    return (
      <div>
        { /* <h1>{JSON.stringify(model.data?.order)}</h1> */}
        <RadioGroup onValueChange={(e) => setProvider(e as PAYMENT_PROVIDER_KEY)} >
          {Object.keys(PAYMENT_PROVIDER).map(item =>
            <div key={`radio-group-${item}`} className="flex items-center space-x-1">
              <RadioGroupItem className="w-[24px] h-[24px]" value={item} id={item} />
              <Label htmlFor={item}>{item}</Label>
            </div>
          )}
        </RadioGroup>
        {provider &&
          <section>
            {model.data.order.order_items && model.data.order.order_items.length > 0
              ? <div className="flex flex-col gap-2" >{model.data.order.order_items.map(item =>
                <OrderItemView objectStoreRoute={objectStoreRoute} {...item} />
              )}</div>
              : <h1>Not found items. Add items to cart first!</h1>
            }
            {(() => {
              switch (provider) {
                case PAYMENT_PROVIDER.STRIPE:
                  // TODO: this not allow fire a POST payment-method
                  return <StripeSession stripePubkey={stripePubkey} paymentRoute={paymentRoute} />
                default:
                  return <div>Not supported provider: {provider}</div>
              }
            })()}
          </section>
        }
      </div>
    )
  }
}
