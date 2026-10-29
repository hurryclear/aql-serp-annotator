import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import Select, { type SelectChangeEvent } from '@mui/material/Select';

interface SelectorProps {
    label: string;
    options: string[];
    value: string;
    onChange: (value: string) => void;
    error?: boolean;
}

function Selector({ label, options, value, onChange, error = false }: SelectorProps) {
    const labelId = `${label}-select-label`;

    const handleChange = (event: SelectChangeEvent) => {
        onChange(event.target.value);
    };

    return (
        <FormControl variant="standard" fullWidth error={error}>
        <InputLabel id={labelId}>{label}</InputLabel>
        <Select labelId={labelId} value={value} onChange={handleChange}>
            {options.map((option) => (
            <MenuItem key={option} value={option}>
                {option}
            </MenuItem>
            ))}
        </Select>
        </FormControl>
    );
}

export default Selector;