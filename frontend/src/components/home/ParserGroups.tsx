import { useEffect, useState } from "react";
import type { ParserOutput, ParserSummary } from "../../types/parser";
import { getParserSummary, listParsers } from "../../api/parsers";
import { getFeatureTypes } from "../../api/featureTypes";
import { filterSummary } from "./parserSummary";
import { Box, Button, Collapse, IconButton, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import InlineError from "../InlineError";
import { useNavigate } from "react-router-dom";
import { tokens } from "../../theme";

function ParserGroups({ provider }: { provider: string }) {
    const [rows, setRows] = useState<ParserSummary[] | null>(null);
    const [labels, setLabels] = useState<Record<string, string>>({});
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        getParserSummary()
        .then(setRows)
        .catch(() =>
            setError(
            "Couldn't load the parsers. Check that the backend is running, then reload.",
            ),
        );
        getFeatureTypes()
        .then((types) => setLabels(Object.fromEntries(types.map((t) => [t.id, t.label]))),
        )
        .catch(() => {});
    }, []);

    const shown = rows ? filterSummary(rows, provider) : null;

    return (
        <>
            <Typography variant="h5" component="h2">Parsers</Typography>
            <Typography
            variant="body1"
            color="text.secondary"
            sx={{ mt: 0.5, mb: 2 }}
            >
            {provider
                ? `Showing ${provider}. Clear the provider to see more.`
                : "View and design parsers by provider and feature type."}
            </Typography>

            {error && <InlineError>{error}</InlineError>}
            {shown === null && !error && (
            <Typography color="text.secondary">Loading…</Typography>
            )}
            {shown?.length === 0 && (
            <Typography color="text.secondary">
                {provider
                ? `No parsers or annotations for ${provider} yet.`
                : "No parsers or annotations yet."}
            </Typography>
            )}

            {shown && shown.length > 0 && (
            <Table size="small">
                <TableHead>
                <TableRow>
                    <TableCell sx={{ width: 40 }} />
                    <TableCell>Provider</TableCell>
                    <TableCell>Feature type</TableCell>
                    <TableCell align="right">Features</TableCell>
                    <TableCell align="right">Parsers</TableCell>
                    <TableCell />
                </TableRow>
                </TableHead>
                <TableBody>
                {shown.map((r) => (
                    <CoverageRow
                    key={`${r.provider_id}-${r.feature_type}`}
                    row={r}
                    label={labels[r.feature_type] ?? r.feature_type}
                    />
                ))}
                </TableBody>
            </Table>
            )}
        </>
    );
}

function CoverageRow({ row, label }: { row: ParserSummary; label: string }) {
    const navigate = useNavigate();
    const [open, setOpen] = useState(false);
    // loaded the first time the row is opened, then kept
    const [parsers, setParsers] = useState<ParserOutput[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    function toggle() {
        setOpen(!open);
        if (!open && parsers === null) {
        listParsers(row.provider_id, row.feature_type)
            .then(setParsers)
            .catch(() => setError("Couldn't load these parsers."));
        }
    }

    return (
        <>
        <TableRow
            hover
            sx={{ "& > td": { borderBottom: open ? "none" : undefined } }}>
            <TableCell>
            <IconButton
                size="small"
                aria-label={open ? "Hide parsers" : "Show parsers"}
                onClick={toggle}
            >
                {open ? (
                <KeyboardArrowUpIcon fontSize="small" />
                ) : (
                <KeyboardArrowDownIcon fontSize="small" />
                )}
            </IconButton>
            </TableCell>
            <TableCell sx={{ textTransform: "capitalize" }}>
            {row.provider_name}
            </TableCell>
            <TableCell>{label}</TableCell>
            <TableCell align="right">{row.features}</TableCell>
            <TableCell align="right">{row.parsers}</TableCell>
            <TableCell align="right">
            {/* on every row: a type with parsers can still be checked or improved */}
            <Button
                variant="outlined"
                size="small"
                onClick={() =>
                navigate(`/parsers/${row.provider_id}/type/${row.feature_type}`, {
                    state: { provider: row.provider_name },
                })
                }
            >
                Design
            </Button>
            </TableCell>
        </TableRow>
        <TableRow>
            <TableCell
            colSpan={6}
            sx={{ py: 0, ...(open ? {} : { borderBottom: "none" }) }}
            >
            <Collapse in={open} timeout="auto" unmountOnExit>
                <Box
                sx={{
                    ml: 5,
                    mr: 1,
                    my: 1,
                    bgcolor: tokens.subtle,
                    borderRadius: "6px",
                    px: 1.5,
                    py: 1,
                }}
                >
                {error && <InlineError>{error}</InlineError>}
                {parsers === null && !error && (
                    <Typography variant="body2" color="text.secondary">
                    Loading…
                    </Typography>
                )}
                {parsers?.length === 0 && (
                    <Typography variant="body2" color="text.secondary">
                    No parsers yet.
                    </Typography>
                )}
                {parsers && parsers.length > 0 && (
                    <Table size="small">
                    <TableHead>
                        <TableRow>
                        <TableCell>XPath</TableCell>
                        <TableCell align="right">SERPs</TableCell>
                        <TableCell align="right">Years</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {parsers.map((p) => (
                        <TableRow key={p.id}>
                            <TableCell
                            sx={{
                                fontFamily: "ui-monospace, Menlo, monospace",
                                fontSize: 12,
                                userSelect: "all",
                                wordBreak: "break-all",
                            }}
                            >
                            {p.xpath}
                            </TableCell>
                            <TableCell align="right">{p.serps}</TableCell>
                            <TableCell align="right">
                            {p.years.join(", ") || "—"}
                            </TableCell>
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


export default ParserGroups;