import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import Link from "@mui/material/Link";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import InlineError from "../components/InlineError";
import { getAnnotationGroups, listAnnotations } from "../api/annotations";
import { tokens } from "../theme";
import type { AnnotationGroup, AnnotationSummary } from "../types/editor";

// the editor's start: every annotation, grouped by provider and year
function EditorHomePage() {
  const [groups, setGroups] = useState<AnnotationGroup[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnnotationGroups()
      .then(setGroups)
      .catch(() => setError("Couldn't load the annotations. Check that the backend is running, then reload."));
  }, []);

  return (
    <Box sx={{ minHeight: "100%", display: "flex", justifyContent: "center", alignItems: "flex-start", p: 2 }}>
      <Card sx={{ width: "100%", maxWidth: 760, mt: 6 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h5" component="h1">Annotation editor</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5, mb: 2 }}>
            Review and correct saved annotations. Choose a group to open.{" "}
            <Link component={RouterLink} to="/">Back to annotating</Link>
          </Typography>

          {error && <InlineError>{error}</InlineError>}
          {groups === null && !error && <Typography color="text.secondary">Loading…</Typography>}
          {groups?.length === 0 && <Typography color="text.secondary">No annotations yet.</Typography>}

          {groups && groups.length > 0 && (
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
                {groups.map((g) => <GroupRow key={`${g.provider_id}-${g.year}`} group={g} />)}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Box>
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
        <TableCell align="right">
          <Button
            variant="outlined"
            size="small"
            onClick={() => navigate(`/editor/${group.provider_id}/${group.year}`, { state: { provider: group.provider } })}
          >
            Open
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

export default EditorHomePage;
