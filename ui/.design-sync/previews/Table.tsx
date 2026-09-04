import { Badge, Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "job-hunt-ui";

export const ApplicationsTable = () => (
  <Table>
    <TableCaption>Applications updated in the last 30 days.</TableCaption>
    <TableHeader>
      <TableRow>
        <TableHead>Company</TableHead>
        <TableHead>Role</TableHead>
        <TableHead>Stage</TableHead>
        <TableHead>Days</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow>
        <TableCell>Globex</TableCell>
        <TableCell>Senior Frontend Engineer</TableCell>
        <TableCell><Badge>Interviewing</Badge></TableCell>
        <TableCell>12</TableCell>
      </TableRow>
      <TableRow>
        <TableCell>Initech</TableCell>
        <TableCell>Staff Engineer, Platform</TableCell>
        <TableCell><Badge variant="secondary">Screening</Badge></TableCell>
        <TableCell>4</TableCell>
      </TableRow>
      <TableRow>
        <TableCell>Umbrella</TableCell>
        <TableCell>Frontend Lead</TableCell>
        <TableCell><Badge variant="outline">Preparing</Badge></TableCell>
        <TableCell>1</TableCell>
      </TableRow>
      <TableRow>
        <TableCell>Soylent</TableCell>
        <TableCell>Senior Engineer, Web</TableCell>
        <TableCell><Badge variant="destructive">Rejected</Badge></TableCell>
        <TableCell>31</TableCell>
      </TableRow>
    </TableBody>
  </Table>
);
