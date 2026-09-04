import { SidebarMenu, SidebarMenuItem, SidebarMenuSkeleton } from "job-hunt-ui";

export const LoadingNav = () => (
  <div style={{ maxWidth: 260 }}>
    <SidebarMenu>
      <SidebarMenuItem><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
      <SidebarMenuItem><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
      <SidebarMenuItem><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
      <SidebarMenuItem><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
    </SidebarMenu>
  </div>
);

export const WithoutIcons = () => (
  <div style={{ maxWidth: 260 }}>
    <SidebarMenu>
      <SidebarMenuItem><SidebarMenuSkeleton /></SidebarMenuItem>
      <SidebarMenuItem><SidebarMenuSkeleton /></SidebarMenuItem>
      <SidebarMenuItem><SidebarMenuSkeleton /></SidebarMenuItem>
    </SidebarMenu>
  </div>
);
