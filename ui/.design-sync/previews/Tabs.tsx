import { Tabs, TabsContent, TabsList, TabsTrigger } from "job-hunt-ui";

export const ApplicationSections = () => (
  <Tabs defaultValue="posting" style={{ maxWidth: 520 }}>
    <TabsList>
      <TabsTrigger value="posting">Posting</TabsTrigger>
      <TabsTrigger value="analysis">Analysis</TabsTrigger>
      <TabsTrigger value="documents">Documents</TabsTrigger>
      <TabsTrigger value="people">People</TabsTrigger>
    </TabsList>
    <TabsContent value="posting">
      <p style={{ margin: "12px 0 0" }}>
        The captured posting, verbatim and read-only. Checksummed when it was
        captured, so it can be trusted as evidence later.
      </p>
    </TabsContent>
    <TabsContent value="analysis">
      <p style={{ margin: "12px 0 0" }}>The fit assessment.</p>
    </TabsContent>
  </Tabs>
);
