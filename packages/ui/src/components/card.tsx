import type { HTMLAttributes } from "react";
import { cn } from "./cn";

function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-xl bg-card text-card-foreground text-sm py-4 ring-1 ring-foreground/10",
        className,
      )}
      {...props}
    />
  );
}
Card.displayName = "Card";

function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col gap-1.5 px-4", className)}
      {...props}
    />
  );
}
CardHeader.displayName = "CardHeader";

function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("font-medium text-base leading-none", className)}
      {...props}
    />
  );
}
CardTitle.displayName = "CardTitle";

function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}
CardDescription.displayName = "CardDescription";

function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("px-4", className)}
      {...props}
    />
  );
}
CardContent.displayName = "CardContent";

function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center px-4 pt-4 border-t", className)}
      {...props}
    />
  );
}
CardFooter.displayName = "CardFooter";

function CardAction({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center", className)}
      {...props}
    />
  );
}
CardAction.displayName = "CardAction";

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, CardAction };
