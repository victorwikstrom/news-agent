import { Flex, Heading, Text, Button } from "@radix-ui/themes";
import Link from "next/link";

export default function HomePage() {
  return (
    <Flex
      align="center"
      justify="center"
      direction="column"
      gap="6"
      style={{ minHeight: "100vh" }}
    >
      <Heading size="8">News Agent</Heading>
      <Text size="4" color="gray" style={{ maxWidth: 480, textAlign: "center" }}>
        AI-powered news aggregation and summarization. Get personalized daily
        digests delivered to your inbox or Slack.
      </Text>
      <Flex gap="3">
        <Link href="/login">
          <Button variant="outline" size="3">
            Log in
          </Button>
        </Link>
        <Link href="/signup">
          <Button size="3">Get started</Button>
        </Link>
      </Flex>
    </Flex>
  );
}
