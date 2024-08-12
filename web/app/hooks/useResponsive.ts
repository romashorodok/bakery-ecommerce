import { createContext, useContext, useCallback, useMemo } from "react";

export const SizeContext = createContext<{ width: number }>({ width: 0 })

type ScreenCandidateDescriptor = Partial<{
  mobile: JSX.Element,
  desktop: JSX.Element,
}>

const MOBILE = 767

export function useResponsive() {
  const { width } = useContext(SizeContext)

  const renderResponsive = useCallback(({
    mobile,
    desktop
  }: ScreenCandidateDescriptor) => {
    if (width <= MOBILE && mobile)
      return mobile
    else if (width > MOBILE || desktop)
      return desktop

    throw new Error("Not found renderer size for component")
  }, [width])

  const mobile = useMemo<boolean>(() => width <= MOBILE, [width])

  return { renderResponsive, mobile }
}

