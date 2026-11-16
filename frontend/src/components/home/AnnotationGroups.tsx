import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import InlineError from "../InlineError";
import { getAnnotationGroups, listAnnotations } from "../../api/annotations";
import { tokens } from "../../theme";
import { filterGroups } from "./filterGroups";
import type { AnnotationGroup, AnnotationSummary } from "../../types/editor";

// what the form on the left has chosen so far; "" means not chosen
type AnnotationGroupsProps = { provider: string; year: string };

// every saved annotation, grouped by provider and year, narrowed to the form's choice
function AnnotationGroups({ provider, year }: AnnotationGroupsProps) {
  const [groups, setGroups] = useState<AnnotationGroup[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // loaded once each time the start page opens, so new annotations show up;
  // the form only filters what's already here, without asking the backend again
  useEffect(() => {
    getAnnotationGroups()
      .then(setGroups)
      .catch(() => setError("Couldn't load the annotations. Check that the backend is running, then reload."));
  }, []);

  const shown = groups ? filterGroups(groups, provider, year) : null;
  const choice = [provider, year].filter(Boolean).join(" ");

  return (
    <>
      <Typography variant="h5" component="h2">Saved annotations</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5, mb: 2 }}>
        {choice ? `Showing ${choice}. Clear the provider or year to see more.` : "Review, correct or design parsers for a group."}
      </Typography>

      {error && <InlineError>{error}</InlineError>}
      {shown === null && !error && <Typography color="text.secondary">Loading…</Typography>}
      {shown?.length === 0 && (
        <Typography color="text.secondary">{choice ? `No annotations for ${choice} yet.` : "No annotations yet."}</Typography>
      )}

      {shown && shown.length > 0 && (
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: 40 }} />
              <TableCell>Provider</TableCell>
              <TableCell>Year</TableCell>
              <TableCell align="right">Annotation</TableCell>
              <TableCell align="right">Ground truth</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {shown.map((g) => <GroupRow key={`${g.provider_id}-${g.year}`} group={g} />)}
          </TableBody>
        </Table>
      )}
    </>
  );
}

// one group, with an arrow that unfolds its annotations: SERP id and number of features
function GroupRow({ group }: { group: AnnotationGroup }) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  // loaded the first time the row is opened, then kept
  const [annotations, setAnnotations] = useState<AnnotationSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function toggle() {
    setOpen(!open);
    if (!open && annotations === null) {
      listAnnotations(group.provider_id, group.year)
        .then(setAnnotations)
        .catch(() => setError("Couldn't load this group's annotations."));
    }
  }

  return (
    <>
      <TableRow hover sx={{ "& > td": { borderBottom: open ? "none" : undefined } }}>
        <TableCell>
          <IconButton size="small" aria-label={open ? "Hide annotations" : "Show annotations"} onClick={toggle}>
            {open ? <KeyboardArrowUpIcon fontSize="small" /> : <KeyboardArrowDownIcon fontSize="small" />}
          </IconButton>
        </TableCell>
        <TableCell sx={{ textTransform: "capitalize" }}>{group.provider}</TableCell>
        <TableCell>{group.year}</TableCell>
        <TableCell align="right">{group.annotations}</TableCell>
        <TableCell align="right">{group.ground_truth}</TableCell>
        <TableCell align="right" sx={{ whiteSpace: "nowrap" }}>
          <Button
            variant="outlined"
            size="small"
            onClick={() => navigate(`/editor/${group.provider_id}/${group.year}`, { state: { provider: group.provider } })}
          >
            Open
          </Button>
          {/* the next step after reviewing: find xpaths for this group's feature blocks */}
          <Button
            variant="outlined"
            size="small"
            sx={{ ml: 0.75 }}
            onClick={() => navigate(`/parsers/${group.provider_id}/${group.year}`, { state: { provider: group.provider } })}
          >
            Design parsers
          </Button>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={6} sx={{ py: 0, ...(open ? {} : { borderBottom: "none" }) }}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ ml: 5, mr: 1, my: 1, bgcolor: tokens.subtle, borderRadius: "6px", px: 1.5, py: 1 }}>
              {error && <InlineError>{error}</InlineError>}
              {annotations === null && !error && <Typography variant="body2" color="text.secondary">Loading…</Typography>}
              {annotations && (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>SERP id</TableCell>
                      <TableCell align="right">Features</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {annotations.map((a) => (
                      <TableRow key={a.serp_id}>
                        <TableCell sx={{ fontFamily: "ui-monospace, Menlo, monospace", fontSize: 12, userSelect: "all" }}>
                          {a.serp_id}
                        </TableCell>
                        <TableCell align="right">{a.feature_count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default AnnotationGroups;
