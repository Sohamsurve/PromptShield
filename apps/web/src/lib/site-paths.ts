/** Admin screens and the caller copies share one page. Links follow the current site. */
export function sitePaths(pathname: string) {
  const caller = pathname.startsWith("/portal");
  const scans = caller ? "/portal/scans" : "/scans";
  return {
    caller,
    arena: caller ? "/portal/arena" : "/arena",
    redteam: caller ? "/portal/redteam" : "/redteam",
    scans,
    xray: (id: string) => `${scans}/${id}`,
  };
}
