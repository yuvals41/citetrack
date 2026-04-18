import * as LabelPrimitive from "@radix-ui/react-label";
import { Slot } from "@radix-ui/react-slot";
import { createContext, useContext, useId } from "react";
import type { ComponentPropsWithoutRef, HTMLAttributes, Ref } from "react";
import {
  Controller,
  FormProvider,
  useFormContext,
  type ControllerProps,
  type FieldPath,
  type FieldValues,
} from "react-hook-form";
import { cn } from "./cn";
import { Label } from "./label";

const Form = FormProvider;

type FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> = {
  name: TName;
};

const FormFieldContext = createContext<FormFieldContextValue>(
  {} as FormFieldContextValue,
);

function FormField<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({ ...props }: ControllerProps<TFieldValues, TName>) {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  );
}

type FormItemContextValue = {
  id: string;
};

const FormItemContext = createContext<FormItemContextValue>(
  {} as FormItemContextValue,
);

function useFormField() {
  const fieldContext = useContext(FormFieldContext);
  const itemContext = useContext(FormItemContext);
  const { getFieldState, formState } = useFormContext();

  const fieldState = getFieldState(fieldContext.name, formState);

  if (!fieldContext.name) {
    throw new Error("useFormField should be used within <FormField>");
  }

  const { id } = itemContext;

  return {
    id,
    name: fieldContext.name,
    formItemId: `${id}-form-item`,
    formDescriptionId: `${id}-form-item-description`,
    formMessageId: `${id}-form-item-message`,
    ...fieldState,
  };
}

function FormItem({
  className,
  ref,
  ...props
}: HTMLAttributes<HTMLDivElement> & { ref?: Ref<HTMLDivElement> }) {
  const id = useId();

  return (
    <FormItemContext.Provider value={{ id }}>
      <div ref={ref} className={cn("space-y-2", className)} {...props} />
    </FormItemContext.Provider>
  );
}
FormItem.displayName = "FormItem";

function FormLabel({
  className,
  ref,
  ...props
}: ComponentPropsWithoutRef<typeof LabelPrimitive.Root> & {
  ref?: Ref<HTMLLabelElement>;
}) {
  const { error, formItemId } = useFormField();

  return (
    <Label
      ref={ref}
      className={cn(error && "text-destructive", className)}
      htmlFor={formItemId}
      {...props}
    />
  );
}
FormLabel.displayName = "FormLabel";

function FormControl({
  ref,
  ...props
}: ComponentPropsWithoutRef<typeof Slot> & { ref?: Ref<HTMLElement> }) {
  const { error, formItemId, formDescriptionId, formMessageId } =
    useFormField();

  return (
    <Slot
      ref={ref}
      id={formItemId}
      aria-describedby={
        !error
          ? formDescriptionId
          : `${formDescriptionId} ${formMessageId}`
      }
      aria-invalid={!!error}
      {...props}
    />
  );
}
FormControl.displayName = "FormControl";

function FormDescription({
  className,
  ref,
  ...props
}: HTMLAttributes<HTMLParagraphElement> & { ref?: Ref<HTMLParagraphElement> }) {
  const { formDescriptionId } = useFormField();

  return (
    <p
      ref={ref}
      id={formDescriptionId}
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}
FormDescription.displayName = "FormDescription";

function FormMessage({
  className,
  children,
  ref,
  ...props
}: HTMLAttributes<HTMLParagraphElement> & {
  ref?: Ref<HTMLParagraphElement>;
}) {
  const { error, formMessageId } = useFormField();
  const body = error ? String(error.message ?? "") : children;

  if (!body) return null;

  return (
    <p
      ref={ref}
      id={formMessageId}
      className={cn("text-destructive text-xs", className)}
      {...props}
    >
      {body}
    </p>
  );
}
FormMessage.displayName = "FormMessage";

export {
  useFormField,
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
};
