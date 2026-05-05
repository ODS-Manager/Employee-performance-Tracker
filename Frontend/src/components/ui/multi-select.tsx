import * as React from "react"
import { ChevronDown, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"
import { Badge } from "./badge"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "./dropdown-menu"

type MultiSelectOption = string | { value: string; label: string }

interface MultiSelectProps {
  options: MultiSelectOption[]
  selected: string[]
  onChange: (selected: string[]) => void
  placeholder?: string
  maxDisplayed?: number
  className?: string
  disabled?: boolean
}

export function MultiSelect({
  options,
  selected,
  onChange,
  placeholder = "Select items...",
  maxDisplayed = 3,
  className,
  disabled = false,
}: MultiSelectProps) {
  const [open, setOpen] = React.useState(false)

  const getOptionValue = (option: MultiSelectOption) =>
    typeof option === 'string' ? option : option.value

  const getOptionLabel = (option: MultiSelectOption) =>
    typeof option === 'string' ? option : option.label

  const labelMap = React.useMemo(() => {
    return new Map(options.map((option) => [getOptionValue(option), getOptionLabel(option)]))
  }, [options])

  const handleToggle = (option: string) => {
    if (selected.includes(option)) {
      onChange(selected.filter((item) => item !== option))
    } else {
      onChange([...selected, option])
    }
  }

  const handleRemove = (option: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onChange(selected.filter((item) => item !== option))
  }

  const handleClearAll = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange([])
  }

  return (
    <div className={cn("space-y-2", className)}>
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild disabled={disabled}>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between h-auto min-h-10 font-normal"
            disabled={disabled}
          >
            <span className="text-muted-foreground">
              {selected.length === 0
                ? placeholder
                : `${selected.length} selected`}
            </span>
            <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent 
          className="w-[--radix-dropdown-menu-trigger-width] max-h-60 overflow-y-auto"
          align="start"
        >
           {options.map((option) => {
            const optionValue = getOptionValue(option)
            const optionLabel = getOptionLabel(option)
            return (
              <DropdownMenuCheckboxItem
                key={optionValue}
                checked={selected.includes(optionValue)}
                onCheckedChange={() => handleToggle(optionValue)}
                onSelect={(e) => e.preventDefault()}
              >
                {optionLabel}
              </DropdownMenuCheckboxItem>
            )
          })}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Display selected items as badges below */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5 p-2 border rounded-md bg-slate-50">
          {selected.slice(0, maxDisplayed).map((item) => {
            const displayValue = labelMap.get(item) || item
            return (
              <Badge
                key={item}
                variant="secondary"
                className="text-xs pr-1 gap-1"
              >
                {displayValue}
                <button
                  type="button"
                  onClick={(e) => handleRemove(item, e)}
                  className="ml-1 rounded-full hover:bg-slate-300 p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            )
          })}
          {selected.length > maxDisplayed && (
            <Badge variant="outline" className="text-xs">
              +{selected.length - maxDisplayed} more
            </Badge>
          )}
          {selected.length > 1 && (
            <button
              type="button"
              onClick={handleClearAll}
              className="text-xs text-muted-foreground hover:text-foreground ml-auto"
            >
              Clear all
            </button>
          )}
        </div>
      )}
    </div>
  )
}
