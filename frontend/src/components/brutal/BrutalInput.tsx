import type { ComponentProps } from "react";
import { forwardRef } from "react";
import cx from "classnames";

type BrutalInputProps = ComponentProps<"input">;

export const BrutalInput = forwardRef<HTMLInputElement, BrutalInputProps>(
  ({ className, ...rest }, ref) => {
    const classes = cx("brutal-input", className);

    return <input className={classes} ref={ref} {...rest} />;
  }
);
