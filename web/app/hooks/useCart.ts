import { useMutation } from "@tanstack/react-query";
import { useAuthFetch } from "./useAuthFetch";

const addToCartMutationKey = ["add-to-cart"]

export function useAddToCart({ cartRoute }: { cartRoute: string }) {

  const { fetch } = useAuthFetch()

  const addToCartMutation = useMutation({
    mutationKey: addToCartMutationKey,
    mutationFn: async ({ productId, quantity }: { productId: string, quantity: number }) => {
      const response = await fetch(`${cartRoute}/cart-item/${productId}`, {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({
          quantity
        })
      })

      if (!response || !response.ok) {
        const error = await response?.json<{ detail: string }>().catch()
        throw new Error(`Bad add cart item error. Err: ${error?.detail}`)
      }

      return response.json<{}>()
    }
  })

  return { addToCartMutation }
}
