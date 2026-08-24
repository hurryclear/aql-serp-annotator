import { useState } from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import { TextField } from "@mui/material";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import SendIcon from '@mui/icons-material/Send';
import { useNavigate } from "react-router-dom";
import { createCart } from "../api/carts";
import Selector from "../components/Selector";

function LandingPage() {
  const [provider, setProvider] = useState("");
  const [language, setLanguage] = useState("");
  const [year, setYear] = useState("");
  const [createdBy, setCreatedBy] = useState("");
  const navigate = useNavigate();

  async function handleSubmit() {
    try {

        const payload = { provider, language, year: Number(year), created_by: createdBy, batch_size: 25 };
        console.log("sending:", payload);
        const result = await createCart(payload);
        console.log("received:", result);

      if (result.id == null) {
        alert("No SERPs found, please choose again!");
        return;
      }
      navigate(`/workspace/${result.id}`); // what's this? 
    } catch (error) {
      alert("Error with creating cart, try again!")
      console.error(error)
    }
  }
  // how to set those fields are required? provider, language, year, annotator
  return (
    <Card>
      <CardContent>
        <Typography sx={{color: "black"}} variant="h2">AQL SERP Annotation</Typography>
        <Stack spacing={2}>
          <Selector
            label="Provider"
            options={["Google", "Baidu", "Bing", "DuckDuckGo", "Yandex", "Twitter", "Wikipedia", "YouTube", "Google Scholar", "SemanticScholar", "e621", "360", "Weibo"]}
            value={provider}
            onChange={setProvider}
          />
          <Selector
            label="Language"
            options={["Arabic", "Bengali", "German", "English", "Spanish", "French", "Indonesian", "Portuguese", "Russian", "Chinese"]}
            value={language}
            onChange={setLanguage}
          />
          <Selector
            label="Year"
            options={["2010", "2011", "2012", "2013"]}
            value={year}
            onChange={setYear}
          />
          <TextField
            id="standard-basic"
            label="Annotator"
            variant="standard"
            value={createdBy}
            onChange={(e) => setCreatedBy(e.target.value)}
          />
          <Button onClick={handleSubmit} variant="contained" endIcon={<SendIcon />}>
            Let's annotate!
          </Button>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default LandingPage;