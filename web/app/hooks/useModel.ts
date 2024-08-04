import { QueryKey, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

export function hasDifferentValue<F extends Object>(first: F, second: Partial<F>): boolean {
  return Object.keys(first).some((key) => {
    return first[key as keyof F] !== second[key as keyof Partial<F>]
  })
}

type UseModelOptions = {
  id: string,
  key: QueryKey
  route: string,
  fetch: (url: string, init?: RequestInit<any>) => Promise<Response | undefined>,
}

export function useModel<F extends Object>({ key, route, fetch, id }: UseModelOptions) {
  const client = useQueryClient()

  const model = useQuery({
    queryKey: key,
    queryFn: async () => {
      const response = await fetch(`${route}/${id}`)
      if (!response || !response.ok) {
        throw new Error('Something goes wrong...')
      }
      return response
    }
  })

  const updater = useMutation({
    mutationFn: ({ model, mutated }: { model: F, mutated: Partial<F> }) => {
      const atLeastOneMutated = Object.keys(mutated).length >= 1
      if (!atLeastOneMutated) {
        throw new Error("Require at least one mutated field")
      }

      if (!hasDifferentValue(model, mutated)) {
        throw new Error("Require at least one mutated value")
      }

      return fetch(`${route}/${id}`, {
        method: "PATCH",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify(mutated),
      })
    },
    onSuccess: async (data) => {
      return client.setQueryData(key, data)
    }
  })

  return { model, updater }
}
