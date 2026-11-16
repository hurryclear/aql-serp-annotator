import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Field from './Field';
import { rankOptions } from './rankOptions';

interface SelectorProps {
    label: string;
    options: string[];
    value: string;
    onChange: (value: string) => void;
    error?: boolean;
}

// A dropdown you can also type into: typing filters the options ("goo" → Google,
// "202" → the 2020s). Only listed options can be chosen, so a typo can't become a value.
function Selector({ label, options, value, onChange, error = false }: SelectorProps) {
    return (
        <Field label={label}>
            <Autocomplete
                options={options}
                // Autocomplete uses null for "nothing chosen"; the form keeps ""
                value={value || null}
                onChange={(_, chosen) => onChange(chosen ?? '')}
                filterOptions={(all, state) => rankOptions(all, state.inputValue)}
                // Enter picks the first match, so "goo" + Enter chooses Google
                autoHighlight
                openOnFocus
                fullWidth
                slotProps={{ listbox: { sx: { fontSize: 14 } } }}
                renderInput={(params) => <TextField {...params} placeholder="Type or choose…" error={error} />}
            />
        </Field>
    );
}

export default Selector;
