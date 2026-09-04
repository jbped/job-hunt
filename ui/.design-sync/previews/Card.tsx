import {
  Badge,
  Button,
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "job-hunt-ui";

export const ApplicationCard = () => (
  <Card style={{ maxWidth: 380 }}>
    <CardHeader>
      <CardTitle>Senior Frontend Engineer</CardTitle>
      <CardDescription>Globex — Remote (US)</CardDescription>
      <CardAction>
        <Badge>Interviewing</Badge>
      </CardAction>
    </CardHeader>
    <CardContent>
      <p style={{ margin: 0 }}>
        Applied 12 days ago. Resume and cover letter rendered; the recruiter
        screen is scheduled for Thursday.
      </p>
    </CardContent>
    <CardFooter style={{ gap: 8 }}>
      <Button size="sm">Open application</Button>
      <Button size="sm" variant="outline">
        Log an interview
      </Button>
    </CardFooter>
  </Card>
);

export const StatCard = () => (
  <Card style={{ maxWidth: 260 }}>
    <CardHeader>
      <CardDescription>Applications in flight</CardDescription>
      <CardTitle style={{ fontSize: 30 }}>14</CardTitle>
    </CardHeader>
    <CardContent>
      <p style={{ margin: 0 }}>4 awaiting a follow-up for more than a week.</p>
    </CardContent>
  </Card>
);
