import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "~/components/ui/card"
import { AspectRatio } from "~/components/ui/aspect-ratio"
import { PropsWithChildren } from "react"

type Product = { id: string, name: string }

export default function ({ id, name, debug, children }: PropsWithChildren<Product & { debug: boolean }>) {
  return (
    <Card x-chunk="dashboard-01-chunk-0 z-10">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xl font-medium">
          {name}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <div className="text-2xl font-bold">$45</div>

        <AspectRatio ratio={16 / 9} className="bg-muted">
          <img src='/sample.webp' className="rounded-md object-cover w-full h-full" />
        </AspectRatio>

        {debug &&
          <p className="text-xs text-muted-foreground">
            {id}
          </p>
        }
        <section className="self-end">
          {children}
        </section>
      </CardContent>
    </Card>
  )
}
