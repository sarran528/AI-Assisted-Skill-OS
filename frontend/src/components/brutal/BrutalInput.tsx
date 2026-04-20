import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";
import type { Ref } from "react";

type BaseProps = {
  label: string;
  error?: string;
  testId?: string;
  inputRef?: Ref<HTMLInputElement | HTMLTextAreaElement>;
};

type InputProps = BaseProps & {
  multiline?: false;
} & InputHTMLAttributes<HTMLInputElement>;

type TextareaProps = BaseProps & {
  multiline: true;
} & TextareaHTMLAttributes<HTMLTextAreaElement>;

type BrutalInputProps = InputProps | TextareaProps;

export function BrutalInput(props: BrutalInputProps) {
  if ("multiline" in props && props.multiline) {
    const { label, error, testId, inputRef, multiline: _multiline, className, ...rest } = props;
    return (
      <label className="brutal-input-group">
        <span className="brutal-input-group__label">{label}</span>
        <textarea
          ref={inputRef as Ref<HTMLTextAreaElement>}
          data-testid={testId}
          className={`brutal-input brutal-input--textarea ${className ?? ""}`.trim()}
          {...rest}
        />
        {error ? <span className="error-text">{error}</span> : null}
      </label>
    );
  }

  const { label, error, testId, inputRef, className, ...rest } = props;
  return (
    <label className="brutal-input-group">
      <span className="brutal-input-group__label">{label}</span>
      <input
        ref={inputRef as Ref<HTMLInputElement>}
        data-testid={testId}
        className={`brutal-input ${className ?? ""}`.trim()}
        {...rest}
      />
      {error ? <span className="error-text">{error}</span> : null}
    </label>
  );
}
