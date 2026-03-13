import {
  Flex,
  Heading,
  Text,
  Button,
  Card,
  Grid,
  Badge,
  Separator,
  Box,
} from "@radix-ui/themes";
import Link from "next/link";

export default function HomePage() {
  return (
    <Flex direction="column" align="center" style={{ minHeight: "100vh" }}>
      {/* Hero */}
      <Flex
        direction="column"
        align="center"
        justify="center"
        gap="5"
        py="9"
        px="4"
        style={{ maxWidth: 680, textAlign: "center" }}
      >
        <Heading size="9" weight="bold">
          Your daily news, summarized by AI
        </Heading>
        <Text size="4" color="gray">
          Personalized daily digests from RSS feeds across Tech, Sweden, and
          Economy — summarized by Claude and delivered to Slack or email every
          morning.
        </Text>
        <Flex gap="3" mt="2" align="center" wrap="wrap" justify="center">
          <Link href="/signup">
            <Button size="3">Get started for free</Button>
          </Link>
          <Link href="/login">
            <Text size="2" color="gray" style={{ textDecoration: "underline" }}>
              Already have an account? Log in
            </Text>
          </Link>
        </Flex>
      </Flex>

      <Separator size="4" />

      {/* How it works */}
      <Flex
        direction="column"
        align="center"
        gap="5"
        py="9"
        px="4"
        style={{ maxWidth: 900, width: "100%" }}
      >
        <Heading size="7">How it works</Heading>
        <Grid
          columns={{ initial: "1", sm: "3" }}
          gap="4"
          width="100%"
        >
          <Card>
            <Flex direction="column" gap="2">
              <Badge size="2" variant="solid" style={{ width: "fit-content" }}>
                1
              </Badge>
              <Heading size="4">Pick your sources</Heading>
              <Text size="2" color="gray">
                Choose from curated news feeds across categories like Tech,
                Sweden, and Economy.
              </Text>
            </Flex>
          </Card>

          <Card>
            <Flex direction="column" gap="2">
              <Badge size="2" variant="solid" style={{ width: "fit-content" }}>
                2
              </Badge>
              <Heading size="4">Choose your channel</Heading>
              <Text size="2" color="gray">
                Get your digest delivered to Slack or email — wherever you start
                your morning.
              </Text>
            </Flex>
          </Card>

          <Card>
            <Flex direction="column" gap="2">
              <Badge size="2" variant="solid" style={{ width: "fit-content" }}>
                3
              </Badge>
              <Heading size="4">Get your digest</Heading>
              <Text size="2" color="gray">
                Wake up to a concise AI summary every morning — no noise, just
                the news that matters.
              </Text>
            </Flex>
          </Card>
        </Grid>
      </Flex>

      <Separator size="4" />

      {/* Digest Preview */}
      <Flex
        direction="column"
        align="center"
        gap="5"
        py="9"
        px="4"
        style={{ maxWidth: 680, width: "100%" }}
      >
        <Heading size="7">Here&apos;s what your digest looks like</Heading>
        <Card style={{ width: "100%" }}>
          <Flex direction="column" gap="4">
            <Heading size="4">
              📰 News Digest – Friday March 13 · 6 articles
            </Heading>

            <Separator size="4" />

            <Flex direction="column" gap="2">
              <Text weight="bold" size="3">🇸🇪 Sweden</Text>
              <Box pl="2">
                <Text as="p" size="2">
                  • <Text weight="bold">Riksbanken signals new rate decision in April</Text>{" "}
                  — The central bank held rates steady but hinted at a possible
                  cut at the next meeting, citing slowing inflation.{" "}
                  <Text size="1" color="blue">Read more →</Text>
                </Text>
                <Text as="p" size="2" mt="1">
                  • <Text weight="bold">Stockholm plans high-speed rail expansion</Text>{" "}
                  — A new proposal would connect Stockholm and Gothenburg in
                  under two hours, with construction starting in 2028.{" "}
                  <Text size="1" color="blue">Read more →</Text>
                </Text>
              </Box>
            </Flex>

            <Separator size="4" />

            <Flex direction="column" gap="2">
              <Text weight="bold" size="3">💻 Tech</Text>
              <Box pl="2">
                <Text as="p" size="2">
                  • <Text weight="bold">OpenAI releases GPT-5 with real-time reasoning</Text>{" "}
                  — The new model shows significant improvements in multi-step
                  reasoning tasks, outperforming previous versions.{" "}
                  <Text size="1" color="blue">Read more →</Text>
                </Text>
                <Text as="p" size="2" mt="1">
                  • <Text weight="bold">EU agrees on landmark AI regulation framework</Text>{" "}
                  — The regulation introduces mandatory risk assessments for
                  high-risk AI systems deployed in the EU.{" "}
                  <Text size="1" color="blue">Read more →</Text>
                </Text>
              </Box>
            </Flex>

            <Separator size="4" />

            <Text size="1" color="gray">
              Generated by Claude · SVT Nyheter, TechCrunch
            </Text>
          </Flex>
        </Card>
      </Flex>

      <Separator size="4" />

      {/* Footer CTA */}
      <Flex
        direction="column"
        align="center"
        gap="4"
        py="9"
        px="4"
        style={{ textAlign: "center" }}
      >
        <Heading size="6">Ready to get started?</Heading>
        <Link href="/signup">
          <Button size="3">Create your free account</Button>
        </Link>
      </Flex>
    </Flex>
  );
}
