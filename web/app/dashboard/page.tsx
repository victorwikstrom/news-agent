import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Box, Card, Flex, Heading, Text } from "@radix-ui/themes";
import SignOutButton from "./sign-out-button";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <Flex align="center" justify="center" style={{ minHeight: "100vh" }}>
      <Box style={{ width: "100%", maxWidth: 500 }} px="4">
        <Card size="4">
          <Flex direction="column" gap="4">
            <Heading size="6">Dashboard</Heading>
            <Text size="2" color="gray">
              Signed in as <strong>{user.email}</strong>
            </Text>
            <Text size="2" color="gray">
              Dashboard coming in phase 2c.
            </Text>
            <SignOutButton />
          </Flex>
        </Card>
      </Box>
    </Flex>
  );
}
