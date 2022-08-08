def goal_evaluation_summary_dict(
    user_package, user_sub_package, package_duration, package_completion_text
):
    return {
        "package_name": user_package.name,
        "sub_package_name": user_sub_package.name,
        "sub_package_duration": f"{package_duration} weeks",
        "package_completion_text": package_completion_text,
    }
