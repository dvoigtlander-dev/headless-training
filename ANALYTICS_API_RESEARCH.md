# Analytics API Research for Training Platforms

## Goal
Determine if Trailhead, Pluralsight, and O'Reilly have public analytics/enrollment APIs that can be accessed for real-time dashboard data.

## Findings

### 1. Trailhead (Salesforce)
**Status:** ❓ Needs investigation

**Possible approaches:**
- Trailhead Learning Hub API - check if available
- Salesforce Org Reports API - if Trailhead is connected to your org
- Admin console exports - manual data pulls
- Trailhead community/org endpoints

**Research needed:**
- [ ] Do you have Trailhead set up as a managed package in your Salesforce org?
- [ ] Can you access Trailhead reports via Salesforce Reports API?
- [ ] Does Trailhead Learning Hub expose analytics endpoints?

**Relevant docs to check:**
- Salesforce API docs for reporting
- Trailhead admin docs for analytics/reporting

---

### 2. Pluralsight
**Status:** ❓ Needs investigation

**Possible approaches:**
- Pluralsight API (if you have organizational account)
- Admin reporting dashboard exports
- SSO integration for data access

**Research needed:**
- [ ] Do you have Pluralsight organizational/admin account?
- [ ] Can you generate API credentials in Pluralsight console?
- [ ] Does Pluralsight expose learner analytics API?

**Relevant docs to check:**
- Pluralsight API documentation
- Pluralsight admin console settings

---

### 3. O'Reilly
**Status:** ❓ Needs investigation

**Possible approaches:**
- O'Reilly API for enterprise accounts
- Learning Platform REST API
- Admin reporting exports

**Research needed:**
- [ ] Do you have O'Reilly enterprise/organizational account?
- [ ] Can you access O'Reilly reporting APIs?
- [ ] What analytics data is available?

**Relevant docs to check:**
- O'Reilly Platform API docs
- O'Reilly Learning Platform admin documentation

---

### 4. PlusPlus
**Status:** ✅ Available via MCP

Already have:
- `get_adoption_metrics()` - org-wide metrics
- Can be called directly from Claude Code

---

## Next Steps

### For each platform:

1. **Check your account settings**
   - Log into the platform admin console
   - Look for API keys, reporting, or integrations section
   - Note any available documentation links

2. **Gather credentials needed**
   - API keys
   - API base URLs
   - Required headers/authentication

3. **Test API endpoints**
   - Try sample calls if endpoints are available
   - Document response structure

4. **Report findings**
   - Share which platforms have accessible APIs
   - Provide credentials/access info
   - We'll build MCPs for available APIs

---

## MCP Development Plan

Once APIs are confirmed available:

```
For each platform with API:
1. Create analytics_mcp.py (e.g., trailhead_analytics_mcp.py)
2. Implement tool functions:
   - get_enrollment_analytics()
   - get_learner_metrics()
   - get_completion_data()
3. Register in ~/.claude/.mcp.json
4. Test with Claude Code
5. Wire into dashboard
```

---

## Questions to Answer

**For Trailhead:**
- Is it set up as org-managed package?
- Can you access via Salesforce org?
- What's your Salesforce instance URL?

**For Pluralsight:**
- Organization name?
- Admin access level?

**For O'Reilly:**
- Enterprise account or free tier?
- Organization name?

