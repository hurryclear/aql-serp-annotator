import { useState } from "react";
import Autocomplete from "@mui/material/Autocomplete";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutlined";
import InlineError from "../InlineError";
import { tokens } from "../../theme";
import type { ParserOutput, TryOutput } from "../../types/parser";

// one feature type annotated on this SERP: its blocks and what they're linked to
export type TypeOnSerp = {
  featureType: string;
  blocks: { node: number | null; parserId: string | null }[];
};

// the last xpath tried on this SERP, and what it found
export type TryResult = { featureType: string; xpath: string; output: TryOutput };

type ParserPanelProps = {
  types: TypeOnSerp[];
  labels: Record<string, string>; // feature type id -> label
  parsers: ParserOutput[];        // the provider's parsers, every type and year
  result: TryResult | null;
  onTry: (featureType: string, xpath: string) => void;
  onSaveNew: (featureType: string, xpath: string) => Promise<boolean>;
  onUse: (parserId: string) => void;
  onDelete: (parserId: string) => void;
  message: string | null;
  notice: string | null;
  busy: boolean;
};

const mono = { fontFamily: "ui-monospace, Menlo, monospace", fontSize: 12 };

function ParserPanel(props: ParserPanelProps) {
  const { types, labels, message, notice } = props;
  return (
    <Card sx={{ width: 380, flexShrink: 0, display: "flex", flexDirection: "column", borderRadius: 1 }}>
      <Stack spacing={1.75} sx={{ p: 1.5, overflowY: "auto", flex: 1 }}>
        <Box>
          <Typography variant="h6" component="h2">Parsers for this SERP</Typography>
          <Typography variant="caption" color="text.secondary">
            Pick an existing parser of this provider (any year) or type a new xpath. Green: annotated blocks. Blue: what
            the xpath finds.
          </Typography>
        </Box>
        {types.length === 0 && (
          <Typography variant="body2" color="text.secondary">This SERP has no annotated feature blocks.</Typography>
        )}
        {types.map((t) => (
          <TypeSection key={t.featureType} {...props} type={t} label={labels[t.featureType] ?? t.featureType} />
        ))}
      </Stack>
      {(message || notice) && (
        <Box sx={{ p: 1.5, pt: 1 }}>
          {message ? <InlineError>{message}</InlineError> : <Typography variant="body2" sx={{ color: "success.main" }}>{notice}</Typography>}
        </Box>
      )}
    </Card>
  );
}

function usedOn(parser: ParserOutput): string {
  return parser.serps === 0 ? "not linked to any SERP" : `used on ${parser.serps} SERP(s) · ${parser.years.join(", ")}`;
}

// one feature type on this SERP: which parser its blocks use, and a box to try, reuse or save one
function TypeSection(props: ParserPanelProps & { type: TypeOnSerp; label: string }) {
  const { type, label, parsers, result, onTry, onSaveNew, onUse, onDelete, busy } = props;
  const candidates = parsers.filter((p) => p.feature_type === type.featureType);
  const [text, setText] = useState("");
  const xpath = text.trim();
  // the box's text is an existing parser's xpath: "use it"; anything else is a new xpath
  const picked = candidates.find((p) => p.xpath === xpath) ?? null;
  const shown = result?.featureType === type.featureType ? result : null;

  return (
    <Box sx={{ borderTop: `0.5px solid ${tokens.border}`, pt: 1.25 }}>
      <Typography variant="subtitle2">{label}</Typography>
      {type.blocks.map((block, i) => {
        const linked = parsers.find((p) => p.id === block.parserId);
        return (
          <Typography key={i} variant="caption" color="text.secondary" component="p" sx={{ wordBreak: "break-all" }}>
            Block {i + 1}{block.node !== null && ` (element ${block.node})`}:{" "}
            {linked ? <Box component="span" sx={{ ...mono, color: "success.main" }}>{linked.xpath}</Box> : "no parser yet"}
          </Typography>
        );
      })}

      <Autocomplete
        freeSolo
        size="small"
        options={candidates}
        getOptionLabel={(option) => (typeof option === "string" ? option : option.xpath)}
        inputValue={text}
        onInputChange={(_, value) => setText(value)}
        renderOption={({ key, ...optionProps }, option) => (
          <li key={key} {...optionProps}>
            <Box>
              <Typography sx={{ ...mono, wordBreak: "break-all" }}>{option.xpath}</Typography>
              <Typography variant="caption" color="text.secondary">{usedOn(option)}</Typography>
            </Box>
          </li>
        )}
        renderInput={(params) => (
          <TextField
            {...params}
            placeholder={candidates.length ? `Pick one of ${candidates.length} parser(s), or type a new xpath` : "Type a new xpath"}
            sx={{ "& input": mono }}
          />
        )}
        sx={{ mt: 1 }}
      />
      {picked && (
        <Typography variant="caption" color="text.secondary" component="p" sx={{ mt: 0.5 }}>Existing parser, {usedOn(picked)}</Typography>
      )}

      <Stack direction="row" spacing={0.75} sx={{ mt: 1, alignItems: "center" }}>
        <Button size="small" variant="outlined" disabled={busy || !xpath} onClick={() => onTry(type.featureType, xpath)}>
          Parse this SERP
        </Button>
        {picked ? (
          <>
            <Button size="small" variant="contained" disabled={busy} onClick={() => onUse(picked.id)}>Use this parser</Button>
            <IconButton size="small" aria-label="Delete parser" disabled={busy} onClick={() => onDelete(picked.id)}>
              <DeleteOutlineIcon fontSize="small" />
            </IconButton>
          </>
        ) : (
          <Button
            size="small"
            variant="contained"
            disabled={busy || !xpath}
            onClick={async () => { if (await onSaveNew(type.featureType, xpath)) setText(""); }}
          >
            Save as new parser
          </Button>
        )}
      </Stack>

      {shown && (
        <Box sx={{ mt: 1, bgcolor: tokens.subtle, borderRadius: "6px", px: 1, py: 0.75 }}>
          <Typography sx={{ ...mono, color: "text.secondary", wordBreak: "break-all" }}>{shown.xpath}</Typography>
          <Typography variant="body2" sx={{ color: shown.output.missed.length || shown.output.extra.length ? "error.main" : "success.main" }}>
            <b>{shown.output.matched.length}</b> found · <b>{shown.output.missed.length}</b> missed · <b>{shown.output.extra.length}</b> extra
          </Typography>
        </Box>
      )}
    </Box>
  );
}

export default ParserPanel;
