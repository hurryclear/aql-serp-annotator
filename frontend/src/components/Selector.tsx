import MenuItem from '@mui/material/MenuItem';
import Select, { type SelectChangeEvent } from '@mui/material/Select';
import Field from './Field';
import { tokens } from '../theme';

interface SelectorProps {
    label: string;
    options: string[];
    value: string;
    onChange: (value: string) => void;
    error?: boolean;
}

function Selector({ label, options, value, onChange, error = false }: SelectorProps) {
    const handleChange = (event: SelectChangeEvent) => {
        onChange(event.target.value);
    };

    return (
        <Field label={label}>
            <Select
                value={value}
                onChange={handleChange}
                error={error}
                fullWidth
                displayEmpty
                renderValue={(selected) => selected || <span style={{ color: tokens.textMuted }}>Choose…</span>}
            >
                {options.map((option) => (
                    <MenuItem key={option} value={option} sx={{ fontSize: 14 }}>
                        {option}
                    </MenuItem>
                ))}
            </Select>
        </Field>
    );
}

export default Selector;
