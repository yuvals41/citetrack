import { UserButton, useUser } from "@clerk/react";
import { useLocation } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Inbox,
  LayoutDashboard,
  MessageSquareQuote,
  Plug,
  Search as SearchIcon,
  Settings,
  Swords,
  Tag,
  Users,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@citetrack/ui/sidebar";
import { Button } from "@citetrack/ui/button";
import { Skeleton } from "@citetrack/ui/skeleton";
import { WorkspaceSwitcher } from "./workspace-switcher";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const personalNavItems: NavItem[] = [
  { label: "Inbox", href: "/dashboard/inbox", icon: Inbox },
  { label: "My Tracking", href: "/dashboard", icon: LayoutDashboard },
];

const workspaceNavItems: NavItem[] = [
  { label: "Brands", href: "/dashboard/brands", icon: Tag },
  { label: "Competitors", href: "/dashboard/competitors", icon: Swords },
  { label: "Prompts", href: "/dashboard/prompts", icon: MessageSquareQuote },
  { label: "Scans", href: "/dashboard/scans", icon: Activity },
];

const configureNavItems: NavItem[] = [
  { label: "Integrations", href: "/dashboard/integrations", icon: Plug },
  { label: "Team", href: "/dashboard/team", icon: Users },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
];

function NavGroup({
  label,
  items,
  currentPathname,
}: {
  label?: string;
  items: NavItem[];
  currentPathname: string;
}) {
  return (
    <SidebarGroup>
      {label ? <SidebarGroupLabel>{label}</SidebarGroupLabel> : null}
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = currentPathname === item.href;
            return (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton asChild isActive={isActive}>
                  <a href={item.href}>
                    <Icon className="size-4" />
                    <span>{item.label}</span>
                  </a>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}

function UserFooter() {
  const { user, isLoaded } = useUser();

  if (!isLoaded) {
    return (
      <div className="border-t pt-2 flex items-center gap-2.5 px-2 py-1.5">
        <Skeleton className="size-7 rounded-full" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-32" />
        </div>
      </div>
    );
  }

  return (
    <div className="border-t pt-2 flex items-center gap-2.5 px-2 py-1.5">
      <UserButton appearance={{ elements: { avatarBox: "size-7" } }} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium leading-tight">
          {user?.fullName ?? user?.firstName ?? "Signed in"}
        </p>
        <p className="truncate text-xs text-muted-foreground leading-tight">
          {user?.primaryEmailAddress?.emailAddress}
        </p>
      </div>
    </div>
  );
}

export function AppSidebar() {
  const location = useLocation();

  return (
    <Sidebar>
      <SidebarHeader>
        <WorkspaceSwitcher />
        <Button
          variant="ghost"
          className="w-full justify-start gap-2 h-9 text-sm text-muted-foreground"
        >
          <SearchIcon className="size-4" />
          Search...
          <kbd className="ml-auto text-[10px] font-mono bg-muted px-1.5 py-0.5 rounded">
            ⌘K
          </kbd>
        </Button>
      </SidebarHeader>
      <SidebarContent>
        <NavGroup items={personalNavItems} currentPathname={location.pathname} />
        <NavGroup
          label="Workspace"
          items={workspaceNavItems}
          currentPathname={location.pathname}
        />
        <NavGroup
          label="Configure"
          items={configureNavItems}
          currentPathname={location.pathname}
        />
      </SidebarContent>
      <SidebarFooter>
        <UserFooter />
      </SidebarFooter>
    </Sidebar>
  );
}
