import React from "react";
import Layout from "@theme/Layout";
import HomepageHero from "../components/HomepageHero";
import FeatureGrid from "../components/FeatureGrid";
import AuthPatternsSection from "../components/AuthPatternsSection";
import HostingSection from "../components/HostingSection";
import QuickStartSection from "../components/QuickStartSection";

const DESCRIPTION =
  "Production-ready FastAPI patterns for JWT authentication, Azure Managed Identity, and Microsoft Entra ID — with a fully working Books API demo.";

export default function Home(): React.ReactElement {
  return (
    <Layout
      title="FastAPI on Azure — Auth & Deployment Patterns"
      description={DESCRIPTION}
    >
      <HomepageHero />
      <FeatureGrid />
      <AuthPatternsSection />
      <HostingSection />
      <QuickStartSection />
    </Layout>
  );
}
