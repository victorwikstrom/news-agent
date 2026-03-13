import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Box, Flex, Heading, Text } from "@radix-ui/themes";
import SignOutButton from "./sign-out-button";
import DashboardForm from "./DashboardForm";
import { Subscription } from "@/lib/types";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const { data: subscription } = await supabase
    .from("subscriptions")
    .select("*")
    .eq("user_id", user.id)
    .maybeSingle();

  const { data: userSources } = await supabase
    .from("user_sources")
    .select("source_id")
    .eq("user_id", user.id);

  const initialSourceIds = (userSources ?? []).map(
    (row: { source_id: string }) => row.source_id
  );

  return (
    <Flex align="start" justify="center" style={{ minHeight: "100vh" }} py="8">
      <Box style={{ width: "100%", maxWidth: 600 }} px="4">
        <Flex direction="column" gap="6">
          <Flex justify="between" align="center">
            <div>
              <Heading size="6">Dashboard</Heading>
              <Text size="2" color="gray">
                {user.email}
              </Text>
            </div>
            <SignOutButton />
          </Flex>

          <DashboardForm
            userEmail={user.email ?? ""}
            initialSubscription={subscription as Subscription | null}
            initialSourceIds={initialSourceIds}
          />
        </Flex>
      </Box>
    </Flex>
  );
}
