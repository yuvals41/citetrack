import type { HTMLAttributes, Ref, TdHTMLAttributes, ThHTMLAttributes } from "react";
import { cn } from "./cn";

function Table({
  className,
  ref,
  ...props
}: HTMLAttributes<HTMLTableElement> & { ref?: Ref<HTMLTableElement> }) {
  return (
    <div className="relative w-full overflow-auto">
      <table
        ref={ref}
        className={cn("w-full caption-bottom text-sm", className)}
        {...props}
      />
    </div>
  );
}
Table.displayName = "Table";

function TableHeader({
  className,
  ref,
  ...props
}: HTMLAttributes<HTMLTableSectionElement> & {
  ref?: Ref<HTMLTableSectionElement>;
}) {
  return (
    <thead
      ref={ref}
      className={cn("[&_tr]:border-b", className)}
      {...props}
    />
  );
}
TableHeader.displayName = "TableHeader";

function TableBody({
  className,
  ref,
  ...props
}: HTMLAttributes<HTMLTableSectionElement> & {
  ref?: Ref<HTMLTableSectionElement>;
}) {
  return (
    <tbody
      ref={ref}
      className={cn("[&_tr:last-child]:border-0", className)}
      {...props}
    />
  );
}
TableBody.displayName = "TableBody";

function TableFooter({
  className,
  ref,
  ...props
}: HTMLAttributes<HTMLTableSectionElement> & {
  ref?: Ref<HTMLTableSectionElement>;
}) {
  return (
    <tfoot
      ref={ref}
      className={cn(
        "border-t bg-muted/50 font-medium [&>tr]:last:border-b-0",
        className,
      )}
      {...props}
    />
  );
}
TableFooter.displayName = "TableFooter";

function TableHead({
  className,
  ref,
  ...props
}: ThHTMLAttributes<HTMLTableCellElement> & {
  ref?: Ref<HTMLTableCellElement>;
}) {
  return (
    <th
      ref={ref}
      className={cn(
        "h-10 px-2 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
        className,
      )}
      {...props}
    />
  );
}
TableHead.displayName = "TableHead";

function TableRow({
  className,
  ref,
  ...props
}: HTMLAttributes<HTMLTableRowElement> & { ref?: Ref<HTMLTableRowElement> }) {
  return (
    <tr
      ref={ref}
      className={cn(
        "border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted",
        className,
      )}
      {...props}
    />
  );
}
TableRow.displayName = "TableRow";

function TableCell({
  className,
  ref,
  ...props
}: TdHTMLAttributes<HTMLTableCellElement> & {
  ref?: Ref<HTMLTableCellElement>;
}) {
  return (
    <td
      ref={ref}
      className={cn(
        "p-2 align-middle [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
        className,
      )}
      {...props}
    />
  );
}
TableCell.displayName = "TableCell";

function TableCaption({
  className,
  ref,
  ...props
}: HTMLAttributes<HTMLTableCaptionElement> & {
  ref?: Ref<HTMLTableCaptionElement>;
}) {
  return (
    <caption
      ref={ref}
      className={cn("mt-4 text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}
TableCaption.displayName = "TableCaption";

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
};
