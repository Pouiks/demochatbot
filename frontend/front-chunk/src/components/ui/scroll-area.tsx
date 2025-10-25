import * as React from "react"

// Mini-implémentation de cn pour éviter les dépendances
const cn = (...classes: (string | undefined | null | false)[]) => classes.filter(Boolean).join(' ');

const ScrollArea = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("overflow-y-auto", className)}
        {...props}
    />
))
ScrollArea.displayName = "ScrollArea"

export { ScrollArea }
