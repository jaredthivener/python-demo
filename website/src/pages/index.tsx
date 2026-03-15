import React from "react";
import Layout from "@theme/Layout";
import HomepageHero from "../components/HomepageHero";
import FeatureGrid from "../components/FeatureGrid";
import AuthPatternsSection from "../components/AuthPatternsSection";
import HostingSection from "../components/HostingSection";
import QuickStartSection from "../components/QuickStartSection";

const DESCRIPTION =
  "A compact FastAPI reference app with a working Books API, rich logging, and balanced AWS, GCP, and Azure guidance.";

export default function Home(): React.ReactElement {
  return (
    <Layout title="Python Demo API" description={DESCRIPTION}>
      <HomepageHero />
      <FeatureGrid />
      <AuthPatternsSection />
      <HostingSection />
      <QuickStartSection />
    </Layout>
  );
}
