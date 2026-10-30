import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutlineOutlined";

function InlineError({ children }: { children: string }) {
  return (
    <Stack direction="row" spacing={0.75} sx={{ alignItems: "flex-start", color: "error.main" }}>
      <ErrorOutlineIcon sx={{ fontSize: 16, mt: "2px" }} aria-hidden />
      <Typography variant="body2" color="inherit">{children}</Typography>
    </Stack>
  );
}

export default InlineError;
