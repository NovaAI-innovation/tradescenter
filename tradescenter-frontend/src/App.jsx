import { useState } from "react";
import {
  AppBar,
  Box,
  Button,
  Container,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  Link,
  Stack,
  ThemeProvider,
  Toolbar,
  Typography,
  createTheme,
} from "@mui/material";
import {
  ArrowForward,
  Bolt,
  Close,
  Construction,
  Email,
  ExpandMore,
  Facebook,
  Instagram,
  LinkedIn,
  Menu,
  Phone,
  Search,
  Security,
  SettingsInputComponent,
  Verified,
  X,
} from "@mui/icons-material";
import logo from "../images/logo.png";
import heroImage from "../images/tradescenter-about-us.jpg";
import kitchenImage from "../images/hero-kitchen.jpg";
import tradesImage from "../images/all-trades.png";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#aa1933",
      dark: "#7d1024",
      contrastText: "#fff",
    },
    secondary: {
      main: "#151515",
    },
    background: {
      default: "#f6f4f1",
      paper: "#fff",
    },
    text: {
      primary: "#151515",
      secondary: "#5f6267",
    },
  },
  typography: {
    fontFamily: '"Montserrat", "Helvetica Neue", Arial, sans-serif',
    h1: {
      fontWeight: 700,
      letterSpacing: "0",
      textTransform: "uppercase",
    },
    h2: {
      fontWeight: 700,
      letterSpacing: "0",
      textTransform: "uppercase",
    },
    h3: {
      fontWeight: 700,
      letterSpacing: "0",
    },
    button: {
      fontWeight: 700,
      letterSpacing: "0",
      textTransform: "uppercase",
    },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          minHeight: 48,
          borderRadius: 2,
          boxShadow: "none",
        },
      },
    },
  },
});

const sizeTokens = {
  nav: {
    utilityIcon: "clamp(0.875rem, 1.2vw, 1.0625rem)",
    logo: {
      xs: "clamp(6.5rem, 24vw, 8rem)",
      sm: "clamp(7.25rem, 20vw, 9rem)",
      md: "clamp(8rem, 11vw, 10rem)",
    },
    toolbarMinHeight: {
      xs: "clamp(3.9rem, 15vw, 4.5rem)",
      md: "clamp(4.5rem, 6vw, 5.25rem)",
    },
  },
  section: {
    py: { xs: "clamp(3rem, 9vw, 4rem)", md: "clamp(4.25rem, 5.5vw, 5.5rem)" },
    gap: { xs: "clamp(1.75rem, 6vw, 2.5rem)", md: "clamp(2.5rem, 4vw, 3.5rem)" },
  },
  hero: {
    minHeight: {
      xs: "clamp(24rem, 56svh, 30rem)",
      md: "clamp(28rem, 44vw, 35rem)",
    },
    title: "clamp(2rem, 5.25vw, 4.35rem)",
    body: "clamp(0.98rem, 1.65vw, 1.2rem)",
  },
  media: {
    projectShadow: "clamp(0.55rem, 1.3vw, 1rem) clamp(0.55rem, 1.3vw, 1rem) 0 #aa1933",
    iconTile: "clamp(2.75rem, 4vw, 3.25rem)",
  },
};

const navItems = [
  { label: "About", dropdown: true },
  { label: "Services", dropdown: true },
  { label: "Projects" },
  { label: "Safety" },
  { label: "Contact" },
];

const services = [
  {
    icon: <Bolt />,
    title: "Electrical Construction",
    body: "Planning, installation, and coordination for residential and commercial builds.",
  },
  {
    icon: <SettingsInputComponent />,
    title: "Systems Integration",
    body: "Lighting, controls, panels, and connected infrastructure delivered with clean handoffs.",
  },
  {
    icon: <Security />,
    title: "Safety First Delivery",
    body: "Field-ready teams, documented practices, and disciplined jobsite communication.",
  },
];

const stats = [
  ["1912", "legacy mindset"],
  ["24/7", "response network"],
  ["100+", "trade categories"],
];

function UtilityBar() {
  return (
    <Box sx={{ bgcolor: "secondary.main", color: "#fff", py: 0.8 }}>
      <Container maxWidth="lg">
        <Stack direction="row" spacing={3} sx={{ alignItems: "center", justifyContent: { xs: "center", sm: "flex-end" } }}>
          <Stack direction="row" spacing={0.75} sx={{ alignItems: "center" }}>
            <Phone sx={{ fontSize: sizeTokens.nav.utilityIcon }} />
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              (630) 288-0200
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1.5} aria-label="social links">
            <Facebook sx={{ fontSize: sizeTokens.nav.utilityIcon }} />
            <X sx={{ fontSize: sizeTokens.nav.utilityIcon }} />
            <Instagram sx={{ fontSize: sizeTokens.nav.utilityIcon }} />
            <LinkedIn sx={{ fontSize: sizeTokens.nav.utilityIcon }} />
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
}

function BrandNav() {
  const [open, setOpen] = useState(false);

  const nav = (
    <Stack direction={{ xs: "column", md: "row" }} spacing={{ xs: 1, md: 3.2 }}>
      {navItems.map((item) => (
        <Link
          href={`#${item.label.toLowerCase()}`}
          key={item.label}
          underline="none"
          sx={{
            color: "text.primary",
            display: "inline-flex",
            alignItems: "center",
            gap: 0.4,
            fontSize: "clamp(0.9375rem, 1.2vw, 1.0625rem)",
            fontWeight: 600,
            py: 1,
            "&:hover": { color: "primary.main" },
          }}
        >
          {item.label}
          {item.dropdown ? <ExpandMore sx={{ fontSize: 18 }} /> : null}
        </Link>
      ))}
    </Stack>
  );

  return (
    <AppBar position="static" color="inherit" elevation={0} sx={{ bgcolor: "#fff", borderBottom: "1px solid #e7e2dc" }}>
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ minHeight: sizeTokens.nav.toolbarMinHeight, justifyContent: "space-between", gap: 3 }}>
          <Box component="a" href="#" sx={{ display: "inline-flex", alignItems: "center", lineHeight: 0 }}>
            <Box
              component="img"
              src={logo}
              alt="TradesCenter"
              sx={{ width: sizeTokens.nav.logo, height: "auto", display: "block" }}
            />
          </Box>

          <Box sx={{ display: { xs: "none", md: "block" } }}>{nav}</Box>

          <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
            <IconButton aria-label="Search">
              <Search />
            </IconButton>
            <IconButton
              aria-label="Open navigation"
              onClick={() => setOpen(true)}
              sx={{ display: { xs: "inline-flex", md: "none" } }}
            >
              <Menu />
            </IconButton>
          </Stack>
        </Toolbar>
      </Container>
      <Drawer anchor="right" open={open} onClose={() => setOpen(false)}>
        <Box sx={{ width: 310, p: 3 }} role="presentation">
          <Stack direction="row" sx={{ mb: 3, justifyContent: "space-between", alignItems: "center" }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Menu
            </Typography>
            <IconButton aria-label="Close navigation" onClick={() => setOpen(false)}>
              <Close />
            </IconButton>
          </Stack>
          {nav}
        </Box>
      </Drawer>
    </AppBar>
  );
}

function AnnouncementBar() {
  return (
    <Box sx={{ bgcolor: "primary.main", color: "#fff", py: { xs: "clamp(1rem, 4vw, 1.35rem)", md: "clamp(1.35rem, 2.4vw, 2rem)" }, textAlign: "center" }}>
      <Typography sx={{ fontSize: "clamp(1rem, 2.5vw, 1.2rem)", fontWeight: 600 }}>
        Ashburn Power & Light is now TradesCenter.{" "}
        <Link href="#about" color="inherit" sx={{ fontWeight: 800, textDecorationColor: "rgba(255,255,255,.7)" }}>
          Learn More &gt;
        </Link>
      </Typography>
    </Box>
  );
}

function Hero() {
  return (
    <Box
      component="section"
      sx={{
        minHeight: sizeTokens.hero.minHeight,
        display: "grid",
        placeItems: "center",
        textAlign: "center",
        color: "#fff",
        position: "relative",
        overflow: "hidden",
        backgroundImage: `linear-gradient(180deg, rgba(30,48,55,.38), rgba(10,13,16,.62)), url(${heroImage})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <Container maxWidth="lg" sx={{ position: "relative", zIndex: 1, py: { xs: 5, md: 7 } }}>
        <Typography
          variant="h1"
          sx={{
            fontSize: sizeTokens.hero.title,
            lineHeight: { xs: 1.02, md: 1.04 },
            maxWidth: "min(58rem, 90vw)",
            mx: "auto",
            textShadow: "0 2px 24px rgba(0,0,0,.35)",
          }}
        >
          Chicago's Leading Electrical Contractor
        </Typography>
        <Typography
          sx={{
            mt: "clamp(1rem, 2.2vw, 1.75rem)",
            fontSize: sizeTokens.hero.body,
            lineHeight: 1.5,
            fontWeight: 600,
            maxWidth: "min(47rem, 88vw)",
            mx: "auto",
          }}
        >
          Since 1912, we've been working with customers to plan projects, innovate solutions, and construct their dream spaces.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          href="#services"
          sx={{ mt: "clamp(2rem, 4vw, 3.25rem)", px: "clamp(1.5rem, 3vw, 2.25rem)", minWidth: "clamp(9rem, 16vw, 10.25rem)", minHeight: "clamp(3rem, 5vw, 3.5rem)" }}
        >
          Learn More
        </Button>
      </Container>
    </Box>
  );
}

function SectionHeader({ kicker, title, body }) {
  return (
    <Stack spacing={1.4} sx={{ maxWidth: 690 }}>
      <Typography sx={{ color: "primary.main", fontWeight: 800, textTransform: "uppercase", fontSize: "clamp(0.75rem, 1vw, 0.8125rem)" }}>
        {kicker}
      </Typography>
      <Typography variant="h2" sx={{ fontSize: "clamp(2rem, 4vw, 2.875rem)", lineHeight: 1.1 }}>
        {title}
      </Typography>
      {body ? (
        <Typography sx={{ color: "text.secondary", fontSize: "clamp(1rem, 1.6vw, 1.125rem)", lineHeight: 1.6, maxWidth: "58ch" }}>
          {body}
        </Typography>
      ) : null}
    </Stack>
  );
}

function ServiceCard({ service }) {
  return (
    <Box
      sx={{
        p: { xs: "clamp(1.35rem, 5vw, 1.75rem)", md: "clamp(1.75rem, 2.6vw, 2.5rem)" },
        bgcolor: "#fff",
        border: "1px solid #e2ded8",
        minHeight: "clamp(12rem, 18vw, 14.25rem)",
        display: "grid",
        alignContent: "space-between",
        transition: "transform 180ms ease, border-color 180ms ease",
        "&:hover": {
          transform: "translateY(-4px)",
          borderColor: "primary.main",
        },
      }}
    >
      <Box
        sx={{
          width: sizeTokens.media.iconTile,
          height: sizeTokens.media.iconTile,
          display: "grid",
          placeItems: "center",
          bgcolor: "primary.main",
          color: "#fff",
          mb: "clamp(1.5rem, 3vw, 2rem)",
        }}
      >
        {service.icon}
      </Box>
      <Stack spacing={1.5}>
        <Typography variant="h3" sx={{ fontSize: "clamp(1.25rem, 2vw, 1.4375rem)" }}>
          {service.title}
        </Typography>
        <Typography sx={{ color: "text.secondary", lineHeight: 1.7 }}>{service.body}</Typography>
      </Stack>
    </Box>
  );
}

function ServicesSection() {
  return (
    <Box id="services" component="section" sx={{ py: sizeTokens.section.py, bgcolor: "background.default" }}>
      <Container maxWidth="lg">
        <Stack spacing={sizeTokens.section.gap}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={4} sx={{ justifyContent: "space-between" }}>
            <SectionHeader
              kicker="Services"
              title="Construction-grade teams for modern electrical work"
              body="TradesCenter pairs field discipline with project visibility, so owners, builders, and trade partners know what is happening next."
            />
            <Button
              variant="outlined"
              color="secondary"
              endIcon={<ArrowForward />}
              href="#contact"
              sx={{ alignSelf: { xs: "flex-start", md: "flex-end" }, px: 3 }}
            >
              Start a Project
            </Button>
          </Stack>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(3, 1fr)" }, gap: 3 }}>
            {services.map((service) => (
              <ServiceCard key={service.title} service={service} />
            ))}
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}

function ProjectsSection() {
  return (
    <Box id="projects" component="section" sx={{ py: sizeTokens.section.py, bgcolor: "#fff" }}>
      <Container maxWidth="lg">
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1.05fr .95fr" }, gap: { xs: 5, md: 8 }, alignItems: "center" }}>
          <Box
            component="img"
            src={kitchenImage}
            alt="Finished kitchen project"
            sx={{
              width: "100%",
              aspectRatio: { xs: "4 / 3", md: "15 / 10" },
              maxHeight: { md: "clamp(21rem, 31vw, 27rem)" },
              objectFit: "cover",
              boxShadow: sizeTokens.media.projectShadow,
            }}
          />
          <Stack spacing={3.5}>
            <SectionHeader
              kicker="Projects"
              title="Built around the job, not the sales pitch"
              body="The remodel keeps the contractor-site hierarchy from the reference: a compact utility layer, a deliberate brand bar, an acquisition notice, and one unmistakable hero claim."
            />
            <Box sx={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 2 }}>
              {stats.map(([value, label]) => (
                <Box key={label} sx={{ borderTop: "3px solid", borderColor: "primary.main", pt: 2 }}>
                  <Typography sx={{ fontSize: "clamp(1.65rem, 3vw, 2.125rem)", fontWeight: 800 }}>{value}</Typography>
                  <Typography sx={{ color: "text.secondary", fontSize: 13, textTransform: "uppercase", fontWeight: 700 }}>
                    {label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Stack>
        </Box>
      </Container>
    </Box>
  );
}

function SafetySection() {
  return (
    <Box id="safety" component="section" sx={{ py: sizeTokens.section.py, bgcolor: "secondary.main", color: "#fff" }}>
      <Container maxWidth="lg">
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: ".85fr 1.15fr" }, gap: 5, alignItems: "center" }}>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
              <Verified sx={{ color: "primary.main" }} />
              <Typography sx={{ fontWeight: 800, textTransform: "uppercase", fontSize: 13 }}>Safety</Typography>
            </Stack>
            <Typography variant="h2" sx={{ fontSize: "clamp(1.95rem, 3.8vw, 2.75rem)", lineHeight: 1.14 }}>
              Clear roles, clean sites, accountable handoffs.
            </Typography>
          </Stack>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)" },
              gap: 2,
            }}
          >
            {["Pre-construction planning", "Licensed trade network", "Owner-ready communication", "Documented safety practices"].map((item) => (
              <Stack
                key={item}
                direction="row"
                spacing={1.5}
                sx={{ border: "1px solid rgba(255,255,255,.18)", p: 2.25, bgcolor: "rgba(255,255,255,.04)", alignItems: "center" }}
              >
                <Construction sx={{ color: "primary.main" }} />
                <Typography sx={{ fontWeight: 700 }}>{item}</Typography>
              </Stack>
            ))}
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

function ContactSection() {
  return (
    <Box id="contact" component="section" sx={{ py: sizeTokens.section.py, bgcolor: "background.default" }}>
      <Container maxWidth="lg">
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, gap: { xs: 4, md: 7 }, alignItems: "center" }}>
          <Stack spacing={3} sx={{ justifyContent: "center" }}>
            <SectionHeader
              kicker="Contact"
              title="Ready for a more disciplined project frontend?"
              body="The new layout is built as reusable MUI sections, with theme tokens controlling color, typography, spacing, and button behavior."
            />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <Button variant="contained" color="primary" startIcon={<Phone />} href="tel:6302880200">
                Call Now
              </Button>
              <Button variant="outlined" color="secondary" startIcon={<Email />} href="mailto:hello@tradescenter.com">
                Email Us
              </Button>
            </Stack>
          </Stack>
          <Box
            component="img"
            src={tradesImage}
            alt="TradesCenter trade professionals"
            sx={{
              width: "100%",
              aspectRatio: { xs: "4 / 3", md: "14 / 9" },
              maxHeight: { md: "clamp(18rem, 26vw, 22rem)" },
              objectFit: "cover",
              bgcolor: "#fff",
            }}
          />
        </Box>
      </Container>
    </Box>
  );
}

function Footer() {
  return (
    <Box component="footer" sx={{ bgcolor: "#0b0b0b", color: "#fff", py: 4 }}>
      <Container maxWidth="lg">
        <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between", alignItems: { xs: "flex-start", md: "center" } }}>
          <Typography sx={{ fontWeight: 700 }}>TradesCenter Electrical Construction Company</Typography>
          <Typography sx={{ color: "rgba(255,255,255,.68)" }}>About / Services / Projects / Safety / Contact</Typography>
        </Stack>
      </Container>
    </Box>
  );
}

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <UtilityBar />
      <BrandNav />
      <AnnouncementBar />
      <Hero />
      <ServicesSection />
      <ProjectsSection />
      <SafetySection />
      <ContactSection />
      <Divider />
      <Footer />
    </ThemeProvider>
  );
}
