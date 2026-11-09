interface SliderFieldProps {
  label: string
  value: number
  min: number
  max: number
  step?: number
  unit?: string
  onChange: (v: number) => void
}

/** 带数值显示的滑块字段 */
export function SliderField({ label, value, min, max, step = 1, unit, onChange }: SliderFieldProps) {
  return (
    <div className="field">
      <div className="field-row">
        <label>{label}</label>
        <span className="val">
          {value}
          {unit ? ` ${unit}` : ''}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  )
}
