from app.config.settings import get_settings, Settings

# Test direct Settings instantiation
direct_settings = Settings()
print("Direct Settings DATABASE_URL:", direct_settings.DATABASE_URL)

# Test get_settings function
cached_settings = get_settings()
print("Cached Settings DATABASE_URL:", cached_settings.DATABASE_URL)

# Check if they're the same object
print("Same object?", direct_settings is cached_settings)

# Check all fields
print("All settings attributes:")
for field_name in direct_settings.__fields__:
    value = getattr(direct_settings, field_name)
    print(f"  {field_name}: {value}")
