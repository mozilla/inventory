alter table user_profiles add column is_desktop_oncall int;
alter table user_profiles add column is_sysadmin_oncall int;
alter table user_profiles add column current_sysadmin_oncall int;
alter table user_profiles add column current_desktop_oncall int;
alter table user_profiles add column irc_nick varchar(128);
