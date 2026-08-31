import type { ChangeEvent, KeyboardEvent } from "react";

type SearchFieldProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  ariaLabel: string;
  onClear?: () => void;
};

export function SearchField({ value, onChange, placeholder, ariaLabel, onClear }: SearchFieldProps) {
  const clear = () => {
    onChange("");
    onClear?.();
  };
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => onChange(event.target.value);
  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape" && value) {
      event.preventDefault();
      clear();
    }
  };

  return <label className="search-field">
    <span className="search-field-icon" aria-hidden="true">⌕</span>
    <span className="sr-only">{ariaLabel}</span>
    <input type="search" value={value} onChange={handleChange} onKeyDown={handleKeyDown} placeholder={placeholder} aria-label={ariaLabel} />
    {value ? <button type="button" className="search-field-clear" aria-label={`Limpiar ${ariaLabel.toLowerCase()}`} onClick={clear}>×</button> : null}
  </label>;
}
